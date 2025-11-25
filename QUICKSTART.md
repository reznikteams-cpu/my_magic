# Quick Start Guide - Wise Guide Bot

Get your bot running in 5 minutes!

## Step 1: Get Your Credentials

### Telegram Bot Token
1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts to create a new bot
4. Copy the token (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXYZ`)

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it (starts with `sk-`)

### Robokassa Credentials
1. Create account at https://www.robokassa.ru/
2. Get your Merchant Login
3. Set Password #1 and Password #2 in settings

## Step 2: Setup Local Environment

```bash
# Clone the project
cd wise_guide_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

## Step 3: Configure .env File

Edit `.env` and add your credentials:

```
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
ROBOKASSA_LOGIN=your_login
ROBOKASSA_PASSWORD1=your_password1
ROBOKASSA_PASSWORD2=your_password2
ROBOKASSA_TEST_MODE=True
SUBSCRIPTION_PRICE=500
SUBSCRIPTION_DAYS=30
```

## Step 4: Run the Bot

Open two terminal windows:

**Terminal 1 - Run the bot:**
```bash
source venv/bin/activate
python bot.py
```

**Terminal 2 - Run the webhook server:**
```bash
source venv/bin/activate
python webhook_server.py
```

You should see:
```
Starting bot...
INFO:telegram.ext._application:Application started
```

## Step 5: Test Your Bot

1. Open Telegram
2. Find your bot (search by name)
3. Send `/start`
4. You should see a welcome message!

## Common Commands to Test

- `/start` - Start the bot
- `/help` - Show help
- `/profile` - Check your profile
- `/subscribe` - See subscription options
- Just type any message to chat with the bot!

## Troubleshooting

### "Token is invalid"
- Check you copied the token correctly from BotFather
- Make sure there are no extra spaces

### "OpenAI API error"
- Verify your API key is correct
- Check you have credits on your OpenAI account
- Ensure the key starts with `sk-`

### "Webhook not receiving payments"
- Make sure webhook server is running in terminal 2
- Check that port 5000 is not blocked by firewall

### "Database error"
- Delete `bot_data.db` file and restart
- This will reset all user data

## Next Steps

1. **Customize the prompt**: Edit `SYSTEM_PROMPT` in `bot.py`
2. **Change subscription price**: Update `SUBSCRIPTION_PRICE` in `.env`
3. **Deploy to production**: See `DEPLOYMENT.md`

## Getting Help

1. Check the logs in your terminal
2. Read `README.md` for detailed documentation
3. Review `DEPLOYMENT.md` for production setup

---

**Enjoy your Wise Guide Bot! 🌙✨**
