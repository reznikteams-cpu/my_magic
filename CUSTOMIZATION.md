# Customization Guide - Wise Guide Bot

Learn how to customize the bot to match your needs.

## System Prompt Customization

The bot's personality is defined by the `SYSTEM_PROMPT` in `bot.py`. To customize:

1. Open `bot.py`
2. Find the `SYSTEM_PROMPT` variable
3. Replace the text with your custom prompt

### Example: Change to a Different Persona

```python
SYSTEM_PROMPT = """You are a helpful assistant specializing in Python programming.
You provide clear, concise explanations with code examples.
Always ask clarifying questions if needed."""
```

### Tips for Better Prompts

- **Be specific**: Define the bot's role clearly
- **Set tone**: Specify how the bot should communicate (formal, casual, poetic, etc.)
- **Give examples**: Include sample responses
- **Set boundaries**: Specify what the bot should and shouldn't do

## Subscription Configuration

### Change Price

Edit `.env`:
```
SUBSCRIPTION_PRICE=1000  # Price in RUB
```

### Change Duration

Edit `.env`:
```
SUBSCRIPTION_DAYS=60  # Subscription lasts 60 days
```

### Different Subscription Tiers

Modify `bot.py` to support multiple tiers:

```python
SUBSCRIPTION_TIERS = {
    "basic": {"price": 300, "days": 30, "name": "Basic"},
    "pro": {"price": 500, "days": 30, "name": "Pro"},
    "premium": {"price": 1000, "days": 60, "name": "Premium"}
}
```

Then update the subscription button handler:

```python
async def handle_subscribe(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("💫 Basic (300 RUB)", callback_data="subscribe_basic")],
        [InlineKeyboardButton("⭐ Pro (500 RUB)", callback_data="subscribe_pro")],
        [InlineKeyboardButton("✨ Premium (1000 RUB)", callback_data="subscribe_premium")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Choose your subscription:", reply_markup=reply_markup)
```

## Adding New Commands

### Example: Add /stats Command

```python
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics."""
    user_id = update.effective_user.id
    history = db.get_user_history(user_id)
    
    message_count = len(history)
    user_messages = sum(1 for m in history if m["role"] == "user")
    
    stats_text = f"""📊 **Your Statistics:**
    
Total messages: {message_count}
Your messages: {user_messages}
Bot responses: {message_count - user_messages}"""
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

# Add to main():
application.add_handler(CommandHandler("stats", stats_command))
```

## Customizing Bot Responses

### Change Welcome Message

In `start()` function:

```python
welcome_message = """Welcome to my custom bot! 
Feel free to ask me anything."""
```

### Change Help Text

In `help_command()` function:

```python
help_text = """📖 **How to use this bot:**

/start - Start conversation
/help - Show this help
/custom - Your custom command"""
```

## Database Customization

### Add New User Fields

Edit `database.py`:

```python
# In init_tables():
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        birth_date TEXT,  # NEW FIELD
        timezone TEXT,    # NEW FIELD
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
```

Add getter/setter methods:

```python
def update_user_profile(self, user_id: int, birth_date: str, timezone: str) -> None:
    """Update user profile information."""
    conn = self.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET birth_date = ?, timezone = ? WHERE user_id = ?",
            (birth_date, timezone, user_id)
        )
        conn.commit()
    finally:
        conn.close()
```

## API Model Customization

### Use Different OpenAI Models

In `bot.py`:

```python
# Use GPT-3.5 (faster, cheaper)
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
    temperature=0.7,
    max_tokens=1500,
)

# Or use GPT-4 (more capable)
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    temperature=0.7,
    max_tokens=2000,
)
```

### Adjust Response Parameters

```python
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    temperature=0.5,      # Lower = more focused, Higher = more creative
    max_tokens=1000,      # Max response length
    top_p=0.9,           # Nucleus sampling
    frequency_penalty=0.5, # Reduce repetition
    presence_penalty=0.5,  # Encourage new topics
)
```

## UI Customization

### Change Button Appearance

In `handle_subscribe()`:

```python
keyboard = [
    [InlineKeyboardButton("🌙 Subscribe Now", callback_data="subscribe")],
    [InlineKeyboardButton("❓ Learn More", callback_data="help")],
    [InlineKeyboardButton("🎁 Free Trial", callback_data="trial")],
]
```

### Add More Buttons

```python
keyboard = [
    [
        InlineKeyboardButton("Option 1", callback_data="opt1"),
        InlineKeyboardButton("Option 2", callback_data="opt2"),
    ],
    [
        InlineKeyboardButton("Option 3", callback_data="opt3"),
    ],
]
```

## Advanced Customizations

### Add Rate Limiting

```python
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_messages: int = 10, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.user_messages = {}
    
    def is_allowed(self, user_id: int) -> bool:
        now = datetime.now()
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Remove old messages outside window
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if (now - msg_time).seconds < self.window_seconds
        ]
        
        if len(self.user_messages[user_id]) >= self.max_messages:
            return False
        
        self.user_messages[user_id].append(now)
        return True

# Use in handle_message():
rate_limiter = RateLimiter()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text("Too many messages. Please wait a moment.")
        return
    
    # ... rest of the code
```

### Add User Preferences

```python
async def set_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allow users to set preferences."""
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("🌙 Dark Mode", callback_data="pref_dark")],
        [InlineKeyboardButton("💬 Verbose", callback_data="pref_verbose")],
        [InlineKeyboardButton("⚡ Concise", callback_data="pref_concise")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Choose your preferences:",
        reply_markup=reply_markup
    )
```

### Add Admin Commands

```python
ADMIN_IDS = [123456789]  # Your Telegram user ID

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin-only command."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You don't have permission.")
        return
    
    # Admin functionality here
    await update.message.reply_text("Admin panel")
```

## Performance Optimization

### Cache Conversation History

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_history(user_id: int, limit: int = 10):
    return db.get_user_history(user_id, limit)
```

### Batch Process Messages

```python
async def batch_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process multiple messages at once."""
    messages = context.user_data.get("pending_messages", [])
    
    if len(messages) >= 5:
        # Process batch
        for msg in messages:
            # Process each message
            pass
        context.user_data["pending_messages"] = []
```

## Testing Your Customizations

1. **Test locally first**: Run bot.py and webhook_server.py
2. **Send test messages**: Verify responses work as expected
3. **Check logs**: Look for errors in console output
4. **Test payments**: Use Robokassa test mode
5. **Deploy gradually**: Update production after thorough testing

---

**Happy customizing! 🚀**
