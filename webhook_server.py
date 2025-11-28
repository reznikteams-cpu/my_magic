"""
Webhook server for handling Robokassa callbacks.

Что делает:
- Принимает ResultURL от Robokassa
- Проверяет подпись SignatureValue по Паролю#2
- Достаёт Shp_user_id (id телеграм-пользователя)
- Обновляет/продлевает подписку в SQLite
- Шлёт сообщение пользователю в Telegram-чат
"""

import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any

import requests
from flask import Flask, request, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Конфиг из окружения ---

ROBOKASSA_PASSWORD2 = os.getenv("ROBOKASSA_PASSWORD2", "").strip()
DB_PATH = os.getenv("DB_PATH", "bot_data.db")
SUBSCRIPTION_DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

if not ROBOKASSA_PASSWORD2:
    logger.warning("ROBOKASSA_PASSWORD2 is not set!")
if not TELEGRAM_BOT_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN is not set!")


# --- Утилиты для подписи и БД ---


def _format_amount(amount_str: str) -> str:
    """
    Форматирует сумму для подписи.
    
    Robokassa может отправлять 500.0 или 500 или 500.00
    Нам нужно нормализовать это в формат, который использовался при генерации ссылки.
    
    Правило: если есть дробная часть, оставляем её, иначе целое число.
    500.0 -> "500"
    500.50 -> "500.5"
    500 -> "500"
    """
    try:
        # Преобразуем в float и обратно в string
        amount_float = float(amount_str.replace(",", "."))
        
        # Если это целое число, возвращаем без дробной части
        if amount_float == int(amount_float):
            return str(int(amount_float))
        else:
            # Иначе возвращаем с дробной частью, убирая лишние нули
            return str(amount_float).rstrip('0').rstrip('.')
    except (ValueError, AttributeError):
        logger.error(f"Cannot format amount: {amount_str}")
        return str(amount_str)


def _calc_result_signature(data: Dict[str, Any]) -> str:
    """
    Расчёт подписи для ResultURL по правилам Robokassa.

    База:
      OutSum:InvId:Пароль#2[:Shp_key=value...]

    Shp_* берутся из пришедших параметров, сортируются по имени.
    """
    out_sum = _format_amount(str(data.get("OutSum", "")))
    inv_id = str(data.get("InvId", ""))

    parts = [out_sum, inv_id, ROBOKASSA_PASSWORD2]

    shp_items = {k: str(v) for k, v in data.items() if k.startswith("Shp_")}
    for key in sorted(shp_items.keys()):
        parts.append(f"{key}={shp_items[key]}")

    base = ":".join(parts)
    logger.debug(f"Result signature base: {base}")
    signature = hashlib.md5(base.encode("utf-8")).hexdigest()
    logger.debug(f"Calculated signature: {signature}")
    return signature


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables_exist() -> None:
    """
    Создаём минимально необходимые таблицы, если их ещё нет.

    Если у тебя уже есть более сложная схема — она не сломается:
    CREATE TABLE IF NOT EXISTS просто ничего не сделает, если таблица уже есть.
    """
    conn = _get_db_connection()
    cur = conn.cursor()

    # Таблица подписок
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            expires_at TEXT NOT NULL
        )
        """
    )

    # Таблица платежей (для истории)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_id TEXT,
            user_id INTEGER,
            amount REAL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def _activate_or_extend_subscription(user_id: int, out_sum: float, inv_id: str) -> str:
    """
    Активирует или продлевает подписку пользователю.

    Возвращает строку с новой датой окончания подписки (ISO-строка).
    """
    _ensure_tables_exist()
    conn = _get_db_connection()
    cur = conn.cursor()

    now = datetime.utcnow()

    # Считываем текущую подписку
    cur.execute(
        "SELECT id, expires_at FROM subscriptions WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()

    if row:
        try:
            current_expires = datetime.fromisoformat(row["expires_at"])
        except Exception:
            current_expires = now

        if current_expires > now:
            new_expires = current_expires + timedelta(days=SUBSCRIPTION_DAYS)
        else:
            new_expires = now + timedelta(days=SUBSCRIPTION_DAYS)

        cur.execute(
            "UPDATE subscriptions SET is_active = 1, expires_at = ? WHERE id = ?",
            (new_expires.isoformat(), row["id"]),
        )
        logger.info(f"Extended subscription for user {user_id} until {new_expires.isoformat()}")
    else:
        new_expires = now + timedelta(days=SUBSCRIPTION_DAYS)
        cur.execute(
            """
            INSERT INTO subscriptions (user_id, is_active, expires_at)
            VALUES (?, 1, ?)
            """,
            (user_id, new_expires.isoformat()),
        )
        logger.info(f"Created new subscription for user {user_id} until {new_expires.isoformat()}")

    # Записываем платёж в историю
    cur.execute(
        """
        INSERT INTO payments (inv_id, user_id, amount, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            inv_id or "",
            user_id,
            out_sum,
            "completed",
            now.isoformat(),
        ),
    )
    logger.info(f"Recorded payment: inv_id={inv_id}, user_id={user_id}, amount={out_sum}")

    conn.commit()
    conn.close()

    return new_expires.isoformat()


def _send_telegram_message(chat_id: int, text: str) -> bool:
    """
    Отправка сообщения в Telegram-чат после успешной оплаты.
    
    Возвращает True если успешно, False если ошибка.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set, cannot send Telegram message")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        logger.info(f"Sending Telegram message to chat_id={chat_id}")
        resp = requests.post(url, json=payload, timeout=10)
        
        if resp.status_code == 200:
            logger.info(f"Successfully sent Telegram message to {chat_id}")
            return True
        else:
            logger.error(
                f"Failed to send Telegram message to {chat_id}: {resp.status_code} {resp.text}"
            )
            return False
    except Exception as e:
        logger.exception(f"Error sending Telegram message to {chat_id}: {e}")
        return False


# --- Маршруты Robokassa ---


@app.route("/robokassa/result", methods=["GET", "POST"])
def robokassa_result() -> str:
    """
    ResultURL — сюда Robokassa присылает подтверждение успешной оплаты.

    ВАЖНО:
    - Здесь мы проверяем подпись и только после этого:
        * создаём/продлеваем подписку
        * шлём сообщение пользователю в Telegram
    - В ответ нужно вернуть 'OK{InvId}' (или 'OK', если InvId пустой), чтобы Robokassa
      признала уведомление обработанным.
    """
    # Robokassa может слать как GET, так и POST — берём объединённо
    data = {**request.args.to_dict(), **request.form.to_dict()}
    logger.info(f"Robokassa RESULT received with data: {data}")

    if not ROBOKASSA_PASSWORD2:
        logger.error("ROBOKASSA_PASSWORD2 is not configured")
        abort(500)

    received_sig = str(data.get("SignatureValue", "")).strip()
    if not received_sig:
        logger.error("SignatureValue is missing in Robokassa RESULT")
        abort(400)

    calculated_sig = _calc_result_signature(data)
    
    # Сравниваем без учёта регистра
    if calculated_sig.lower() != received_sig.lower():
        logger.error(
            f"Invalid SignatureValue in RESULT. Received={received_sig} Calculated={calculated_sig}"
        )
        abort(400)

    logger.info("Signature verified successfully")

    # Подпись корректна — можно доверять данным
    out_sum_str = str(data.get("OutSum", "0"))
    try:
        out_sum = float(out_sum_str.replace(",", "."))
    except ValueError:
        out_sum = 0.0
        logger.warning(f"Could not parse OutSum: {out_sum_str}")

    inv_id = str(data.get("InvId", "") or "")

    shp_user_id = data.get("Shp_user_id")
    if not shp_user_id:
        logger.error("Shp_user_id is missing in RESULT — не знаем, к какому чату привязать оплату")
        # Всё равно возвращаем OK, чтобы Robokassa больше не дёргала этот ResultURL
        return f"OK{inv_id}" if inv_id else "OK"

    try:
        user_id = int(shp_user_id)
    except (ValueError, TypeError):
        logger.error(f"Invalid Shp_user_id in RESULT: {shp_user_id}")
        return f"OK{inv_id}" if inv_id else "OK"

    logger.info(f"Processing payment for user_id={user_id}, inv_id={inv_id}, amount={out_sum}")

    # Активируем/продлеваем подписку
    try:
        new_expires_iso = _activate_or_extend_subscription(
            user_id=user_id,
            out_sum=out_sum,
            inv_id=inv_id,
        )
    except Exception as e:
        logger.exception(f"Error activating subscription for user {user_id}: {e}")
        # Всё равно отвечаем OK, чтобы Robokassa не ретрила
        return f"OK{inv_id}" if inv_id else "OK"

    # Уведомляем пользователя в Telegram
    try:
        expires_dt = datetime.fromisoformat(new_expires_iso)
        expires_str = expires_dt.strftime("%d.%m.%Y")
    except Exception:
        expires_str = new_expires_iso

    msg = (
        "✨ <b>Оплата прошла успешно!</b>\n\n"
        f"Ваша подписка активирована до <b>{expires_str}</b>.\n"
        "Спасибо, что вы с нами 💚"
    )
    
    msg_sent = _send_telegram_message(chat_id=user_id, text=msg)
    if not msg_sent:
        logger.warning(f"Failed to send Telegram message to user {user_id}, but subscription was activated")

    # Ответ Robokassa
    # Если InvId пустой, вернём просто "OK"
    response = f"OK{inv_id}" if inv_id else "OK"
    logger.info(f"Returning response to Robokassa: {response}")
    return response


@app.route("/robokassa/success", methods=["GET", "POST"])
def robokassa_success() -> str:
    """
    SuccessURL — сюда пользователь попадает в браузере после успешной оплаты.
    Здесь уже НЕ нужно ничего подтверждать, вся важная логика должна быть в ResultURL.
    """
    logger.info("User redirected to success page")
    return "Оплата прошла успешно. Можете вернуться в Telegram-бот 🧡"


@app.route("/robokassa/fail", methods=["GET", "POST"])
def robokassa_fail() -> str:
    """
    FailURL — сюда пользователь попадает после неудачной/отменённой оплаты.
    """
    logger.info("User redirected to fail page")
    return "Оплата не была завершена. Попробуйте ещё раз или свяжитесь с поддержкой."


@app.route("/health", methods=["GET"])
def health_check() -> str:
    """
    Health check endpoint для мониторинга.
    """
    return "OK"


if __name__ == "__main__":
    # Локальный запуск:
    #   python webhook_server.py
    #
    # В проде обычно используется gunicorn/uvicorn, но этот блок не мешает.
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting webhook server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
