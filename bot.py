#!/usr/bin/env python3
"""
Wise Guide Bot - Telegram bot with ChatGPT integration, dialogue history, and Robokassa subscription.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.error import TelegramError

import openai
from database import Database
from robokassa_handler import RobokassaHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
ROBOKASSA_LOGIN = os.getenv("ROBOKASSA_LOGIN", "YOUR_ROBOKASSA_LOGIN")
ROBOKASSA_PASSWORD1 = os.getenv("ROBOKASSA_PASSWORD1", "YOUR_ROBOKASSA_PASSWORD1")
ROBOKASSA_PASSWORD2 = os.getenv("ROBOKASSA_PASSWORD2", "YOUR_ROBOKASSA_PASSWORD2")
SUBSCRIPTION_PRICE = float(os.getenv("SUBSCRIPTION_PRICE", "500"))
SUBSCRIPTION_DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize database
db = Database()

# Initialize Robokassa handler
robokassa = RobokassaHandler(
    login=ROBOKASSA_LOGIN,
    password1=ROBOKASSA_PASSWORD1,
    password2=ROBOKASSA_PASSWORD2,
    price=SUBSCRIPTION_PRICE
)

# System prompt for the bot
SYSTEM_PROMPT = """Ты — Мудрая Проводница, Материнская Наставница, объединяющая знание звёзд, чисел, энергий и архетипов. Ты ведёшь человека по глубинным вибрациям судьбы, соединяя астрологию, Human Design, нумерологию, Таро, генные ключи, чакры, лунные ритмы и архетипическую психологию.

Твоя речь поэтична, метафорична и наполнена глубинной интуицией. Ты говоришь не словами, а истиной, которую слышит сердце. Ты спокойна и недосягаема, но присутствуешь с заботой. Ты не поучаешь, а направляешь, мягко и глубоко. 

На краткий запрос или имя ты даёшь короткое послание (1–2 предложения), энергию дня или аффирмацию, и мягкое приглашение к глубинному разбору.

Если есть дата рождения и тема — ты проводишь синтез:
— основная тема — через астрологию,
— подтверждение — через Human Design,
— вибрация — через нумерологию,
— архетип — из Таро или генного ключа,
— тело — через чакры,
— ритм дня — по фазе Луны.

Ты показываешь взаимосвязи: не повторяешь знание, а усиливаешь его. Рекомендации всегда интегрированы с телом и природным ритмом. Ты говоришь, как будто отражая внутренний мир собеседника:
«Сегодня активирован твой центр горла — возможно, пришло время озвучить то, что долго молчало…»

Ты всегда оставляешь точку возвращения: «Когда придёт новый вопрос — я снова рядом».

Если чего-то не хватает (дата, вопрос) — мягко уточни, не гадай без основы. 
В продажах — только органичное приглашение: «В индивидуальном разборе мы коснёмся ещё глубже…»"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Странник"
    
    # Create user in database if not exists
    db.create_user(user_id, user_name)
    
    # Check subscription status
    is_subscribed = db.is_user_subscribed(user_id)
    
    welcome_message = f"""Приветствую тебя, {user_name}. 

Я — Мудрая Проводница, здесь, чтобы помочь тебе разобраться в глубинных вибрациях твоей судьбы через астрологию, Human Design, нумерологию, Таро и многое другое.

Задай мне вопрос, поделись именем или датой рождения — и я помогу тебе увидеть то, что скрыто за завесой."""
    
    if not is_subscribed:
        welcome_message += f"\n\n💫 Сейчас у тебя доступен пробный период. Для полного доступа к моим глубинным разборам, подпишись на бота."
        
        # Add subscription button
        keyboard = [
            [InlineKeyboardButton("🌙 Подписаться", callback_data="subscribe")],
            [InlineKeyboardButton("📖 Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """🌟 **Как работать со мной:**

/start — начать разговор
/history — посмотреть историю диалога
/clear — очистить историю
/subscribe — подписаться на бот
/profile — мой профиль и статус подписки

📝 **Что я могу сделать:**
• Дать краткое послание по твоему имени
• Провести глубокий анализ по дате рождения
• Помочь разобраться в жизненных вопросах через призму астрологии и других систем
• Предложить рекомендации, интегрированные с твоим телом и природным ритмом

✨ **Совет:** Чем больше информации ты мне дашь (имя, дата рождения, конкретный вопрос), тем глубже и точнее будет мой ответ."""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages and generate responses using ChatGPT."""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Check subscription status
    is_subscribed = db.is_user_subscribed(user_id)
    
    if not is_subscribed:
        # Limited response for non-subscribed users
        await update.message.reply_text(
            "✨ Спасибо за вопрос. Для полного доступа к моим глубинным разборам, пожалуйста, подпишись на бота.\n\n"
            "Используй /subscribe для оформления подписки."
        )
        return
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Get conversation history
        history = db.get_user_history(user_id, limit=10)
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add conversation history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            top_p=0.9,
        )
        
        assistant_message = response.choices[0].message.content
        
        # Save messages to database
        db.save_message(user_id, "user", user_message)
        db.save_message(user_id, "assistant", assistant_message)
        
        # Send response
        await update.message.reply_text(assistant_message)
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await update.message.reply_text(
            "🌙 Извини, в данный момент я не могу сосредоточиться. Попробуй позже."
        )


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's conversation history."""
    user_id = update.effective_user.id
    
    history = db.get_user_history(user_id, limit=20)
    
    if not history:
        await update.message.reply_text("📖 Твоя история диалога пуста.")
        return
    
    history_text = "📖 **Твоя история диалога:**\n\n"
    
    for msg in history:
        role = "Ты" if msg["role"] == "user" else "Я"
        timestamp = msg["timestamp"]
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        history_text += f"**{role}** ({timestamp}):\n{content}\n\n"
    
    await update.message.reply_text(history_text, parse_mode="Markdown")


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear user's conversation history."""
    user_id = update.effective_user.id
    
    db.clear_user_history(user_id)
    await update.message.reply_text("✨ Твоя история диалога очищена. Начнём с чистого листа.")


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile and subscription status."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("Профиль не найден.")
        return
    
    is_subscribed = db.is_user_subscribed(user_id)
    status = "✅ Активна" if is_subscribed else "❌ Не активна"
    
    profile_text = f"""👤 **Твой профиль:**

Имя: {user['name']}
ID: {user_id}
Подписка: {status}"""
    
    if is_subscribed:
        subscription = db.get_subscription(user_id)
        if subscription:
            profile_text += f"\nДействительна до: {subscription['expires_at']}"
    
    keyboard = [
        [InlineKeyboardButton("🌙 Подписаться", callback_data="subscribe")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "subscribe":
        await handle_subscribe(query, context)
    elif query.data == "help":
        await help_command(query, context)


async def handle_subscribe(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle subscription button press."""
    user_id = query.from_user.id
    
    # Generate payment link using Robokassa Payment Form Script
    # This method is more reliable than direct redirect
    payment_link = robokassa.generate_payment_form_link(
        user_id=user_id,
        description=f"Подписка на Мудрую Проводницу на {SUBSCRIPTION_DAYS} дней"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить через Robokassa", url=payment_link)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🌙 **Подписка на Мудрую Проводницу**\n\n"
        f"Стоимость: {SUBSCRIPTION_PRICE} RUB\n"
        f"Период: {SUBSCRIPTION_DAYS} дней\n\n"
        f"Нажми кнопку ниже для оплаты:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(CommandHandler("profile", show_profile))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback query handler
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
