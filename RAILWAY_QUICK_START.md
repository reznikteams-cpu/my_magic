# Railway Quick Start - 5 Minutes to Live Bot

Deploy your Telegram bot to Railway in just 5 minutes!

## Prerequisites (2 minutes)

You need:
1. ✅ GitHub account with this repository
2. ✅ Telegram bot token (from @BotFather)
3. ✅ OpenAI API key
4. ✅ Robokassa merchant credentials

## Step 1: Create Railway Account (1 minute)

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign in with GitHub
4. Grant Railway access to your repositories

## Step 2: Deploy Project (2 minutes)

1. Click "New Project" in Railway dashboard
2. Select "Deploy from GitHub repo"
3. Search for `my_magic` repository
4. Click to import and deploy

Railway will automatically:
- Detect the Dockerfile
- Build the Docker image
- Deploy both bot and webhook services

## Step 3: Add Environment Variables (1 minute)

1. In Railway dashboard, click on your service
2. Go to "Variables" tab
3. Add these variables:

```
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
ROBOKASSA_LOGIN=your_login
ROBOKASSA_PASSWORD1=your_password1
ROBOKASSA_PASSWORD2=your_password2
ROBOKASSA_TEST_MODE=True
SUBSCRIPTION_PRICE=500
SUBSCRIPTION_DAYS=30
WEBHOOK_PORT=5000
DEBUG=False
```

4. Click "Save"

## Step 4: Get Your URL (1 minute)

1. In Railway dashboard, click on your service
2. Go to "Settings" tab
3. Under "Networking", copy your public URL
4. It looks like: `https://wise-guide-bot-production.up.railway.app`

## Step 5: Configure Robokassa (Optional)

If using Robokassa:

1. Log in to Robokassa merchant account
2. Go to Settings → Notification URLs
3. Set notification URL to:
   ```
   https://your-railway-url/webhook/robokassa/result
   ```

## Step 6: Test Your Bot (1 minute)

1. Open Telegram
2. Find your bot
3. Send `/start`
4. You should see the welcome message!

## Verify Deployment

Check logs in Railway:

1. Click on your service
2. Go to "Logs" tab
3. You should see:
   ```
   Starting webhook server on port 5000
   Starting bot...
   ```

## Troubleshooting

**Bot not responding?**
- Check logs for errors
- Verify token is correct
- Restart service (click "Redeploy")

**Webhook errors?**
- Check logs for 404 errors
- Verify Robokassa URL is correct
- Test with `curl https://your-url/health`

**Need more help?**
- See `RAILWAY_DEPLOYMENT.md` for detailed guide
- Check Railway docs: https://docs.railway.app

## Update Your Bot

To update the bot:

1. Make changes to GitHub
2. Commit and push
3. Railway automatically redeploys
4. Done! ✨

## Next Steps

- ✅ Bot is live!
- ✅ Test all commands
- ✅ Configure Robokassa webhooks
- ✅ Monitor logs regularly
- ✅ Set up alerts (optional)

## Cost

- **Free tier:** 512MB RAM, 100GB bandwidth
- **Paid:** $5-20/month for more resources

Your bot fits easily in the free tier!

---

**Your bot is now live on Railway! 🚀**

For detailed information, see `RAILWAY_DEPLOYMENT.md`
