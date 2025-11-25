# Wise Guide Bot - Telegram Bot with ChatGPT Integration

A sophisticated Telegram bot powered by ChatGPT that acts as a "Wise Guide" (Мудрая Проводница), providing spiritual and astrological guidance. The bot includes dialogue history persistence and a subscription system integrated with Robokassa payment processor.

## Features

- **ChatGPT Integration**: Uses OpenAI's GPT-4 model with a custom system prompt for consistent personality
- **Dialogue History**: Automatically saves and retrieves conversation history for context-aware responses
- **User Management**: Tracks users, their subscription status, and payment history
- **Robokassa Integration**: Secure payment processing with webhook handling for subscription activation
- **SQLite Database**: Local persistence for users, messages, and subscriptions
- **Telegram Commands**: `/start`, `/help`, `/history`, `/clear`, `/profile`, `/subscribe`

## Architecture

The bot consists of three main components:

1. **bot.py** - Main Telegram bot application using `python-telegram-bot` library
2. **database.py** - SQLite database handler for users, messages, and subscriptions
3. **webhook_server.py** - Flask server for handling Robokassa payment webhooks
4. **robokassa_handler.py** - Robokassa payment integration utilities

## Prerequisites

- Python 3.9+
- Telegram Bot Token (from BotFather)
- OpenAI API Key
- Robokassa merchant account with credentials

## Installation

### 1. Clone or download the project

```bash
cd wise_guide_bot
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```
TELEGRAM_BOT_TOKEN=your_token_from_botfather
OPENAI_API_KEY=your_openai_api_key
ROBOKASSA_LOGIN=your_robokassa_login
ROBOKASSA_PASSWORD1=your_robokassa_password1
ROBOKASSA_PASSWORD2=your_robokassa_password2
ROBOKASSA_TEST_MODE=True  # Set to False for production
SUBSCRIPTION_PRICE=500
SUBSCRIPTION_DAYS=30
WEBHOOK_PORT=5000
DEBUG=False
```

## Running the Bot

### Development Mode

Run the bot locally:

```bash
python bot.py
```

In another terminal, run the webhook server:

```bash
python webhook_server.py
```

### Production Deployment

For production, use a process manager like `systemd`, `supervisor`, or `pm2`.

#### Using systemd (Linux)

Create `/etc/systemd/system/wise-guide-bot.service`:

```ini
[Unit]
Description=Wise Guide Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/wise_guide_bot
Environment="PATH=/home/ubuntu/wise_guide_bot/venv/bin"
ExecStart=/home/ubuntu/wise_guide_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/wise-guide-webhook.service`:

```ini
[Unit]
Description=Wise Guide Bot Webhook Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/wise_guide_bot
Environment="PATH=/home/ubuntu/wise_guide_bot/venv/bin"
ExecStart=/home/ubuntu/wise_guide_bot/venv/bin/python webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable wise-guide-bot wise-guide-webhook
sudo systemctl start wise-guide-bot wise-guide-webhook
```

Check status:

```bash
sudo systemctl status wise-guide-bot
sudo systemctl status wise-guide-webhook
```

#### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Build and run:

```bash
docker build -t wise-guide-bot .
docker run -d --name wise-guide-bot --env-file .env wise-guide-bot
```

## Robokassa Integration

### Setting up Robokassa webhooks

1. Log in to your Robokassa merchant account
2. Go to Settings → Notification URL
3. Set the notification URL to: `https://your-domain.com/webhook/robokassa/result`
4. Set the success redirect URL to: `https://your-domain.com/webhook/robokassa/success`
5. Set the fail redirect URL to: `https://your-domain.com/webhook/robokassa/fail`

### Testing payments

When `ROBOKASSA_TEST_MODE=True`, the bot uses Robokassa's test environment. Test card details:

- Card: 4111 1111 1111 1111
- Expiry: Any future date
- CVV: Any 3 digits

## Database Schema

### Users Table
- `user_id` (PRIMARY KEY): Telegram user ID
- `name`: User's first name
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### Messages Table
- `id` (PRIMARY KEY): Message ID
- `user_id` (FOREIGN KEY): User ID
- `role`: "user" or "assistant"
- `content`: Message text
- `timestamp`: Message timestamp

### Subscriptions Table
- `id` (PRIMARY KEY): Subscription ID
- `user_id` (UNIQUE FOREIGN KEY): User ID
- `created_at`: Subscription creation timestamp
- `expires_at`: Subscription expiration timestamp
- `status`: "active" or "expired"

### Payments Table
- `id` (PRIMARY KEY): Payment ID
- `user_id` (FOREIGN KEY): User ID
- `transaction_id`: Robokassa transaction ID
- `amount`: Payment amount in RUB
- `status`: "pending" or "completed"
- `created_at`: Payment creation timestamp
- `completed_at`: Payment completion timestamp

## Bot Commands

- `/start` - Initialize bot and show welcome message
- `/help` - Show help information
- `/history` - Display conversation history (last 20 messages)
- `/clear` - Clear conversation history
- `/profile` - Show user profile and subscription status
- `/subscribe` - Show subscription options

## Customization

### Changing the System Prompt

Edit the `SYSTEM_PROMPT` variable in `bot.py` to customize the bot's personality and behavior.

### Adjusting Subscription Price and Duration

Modify in `.env`:
```
SUBSCRIPTION_PRICE=500
SUBSCRIPTION_DAYS=30
```

### Adding More Commands

Add new command handlers in `bot.py`:

```python
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Your command logic
    pass

application.add_handler(CommandHandler("newcommand", new_command))
```

## Troubleshooting

### Bot doesn't respond to messages

1. Check that `TELEGRAM_BOT_TOKEN` is correct
2. Verify the bot is running: `ps aux | grep bot.py`
3. Check logs: `tail -f bot.log`

### Webhook not receiving payments

1. Ensure webhook server is running on the correct port
2. Verify Robokassa notification URL is correctly configured
3. Check firewall allows incoming connections on webhook port
4. Test with Robokassa test mode first

### OpenAI API errors

1. Verify `OPENAI_API_KEY` is valid and has sufficient credits
2. Check API rate limits
3. Ensure the model "gpt-4" is available on your account

### Database errors

1. Check file permissions on `bot_data.db`
2. Ensure disk space is available
3. Try deleting `bot_data.db` to reinitialize (will lose history)

## Logging

Logs are printed to console. For file logging, modify the logging configuration in `bot.py`:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

## Security Considerations

1. **Never commit `.env` file** with real credentials
2. **Use HTTPS** for webhook URLs in production
3. **Validate all Robokassa signatures** before processing payments
4. **Keep API keys secret** and rotate them regularly
5. **Use strong database passwords** if migrating to PostgreSQL
6. **Enable CORS restrictions** on webhook endpoints

## Performance Optimization

For high-traffic bots, consider:

1. **Migrate to PostgreSQL** instead of SQLite
2. **Add Redis caching** for frequently accessed data
3. **Implement rate limiting** to prevent abuse
4. **Use async/await** for concurrent operations
5. **Add message queuing** (Celery, RabbitMQ) for long-running tasks

## License

This project is provided as-is for personal use.

## Support

For issues or questions, please check the logs and ensure all environment variables are correctly configured.

---

**Created with ❤️ by Manus AI**
