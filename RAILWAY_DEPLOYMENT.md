# Railway Deployment Guide - Wise Guide Bot

Railway is the recommended platform for deploying this Telegram bot because it supports long-running processes, which are essential for the bot to work continuously.

## Why Railway?

- ✅ Supports long-running processes (unlike Vercel)
- ✅ Simple deployment from GitHub
- ✅ Built-in environment variable management
- ✅ Automatic SSL/TLS for webhooks
- ✅ PostgreSQL database support (if needed)
- ✅ Generous free tier (512MB RAM, 100GB bandwidth)
- ✅ Easy scaling and monitoring

## Prerequisites

1. **GitHub Account** - Repository must be on GitHub (already done ✓)
2. **Railway Account** - Sign up at https://railway.app
3. **Telegram Bot Token** - From @BotFather
4. **OpenAI API Key** - From platform.openai.com
5. **Robokassa Credentials** - From your merchant account

## Step-by-Step Deployment

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign in with GitHub (recommended)
4. Grant Railway access to your GitHub repositories

### Step 2: Create New Project

1. In Railway dashboard, click "New Project"
2. Select "Deploy from GitHub repo"
3. Search for `my_magic` repository
4. Click to import it

### Step 3: Configure Environment Variables

Railway will automatically detect the Dockerfile and build the project. Now add environment variables:

1. In the Railway dashboard, go to your project
2. Click on the service (should be named after your repo)
3. Go to "Variables" tab
4. Add the following environment variables:

```
TELEGRAM_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
ROBOKASSA_LOGIN=your_login
ROBOKASSA_PASSWORD1=your_password1
ROBOKASSA_PASSWORD2=your_password2
ROBOKASSA_TEST_MODE=False
SUBSCRIPTION_PRICE=500
SUBSCRIPTION_DAYS=30
WEBHOOK_PORT=5000
DEBUG=False
```

**Important:** Use `ROBOKASSA_TEST_MODE=False` for production, but test with `True` first.

### Step 4: Get Your Public URL

1. In Railway dashboard, click on your service
2. Go to "Settings" tab
3. Under "Networking", you'll see your public URL (e.g., `https://wise-guide-bot-production.up.railway.app`)
4. Copy this URL - you'll need it for Robokassa configuration

### Step 5: Configure Robokassa Webhooks

1. Log in to your Robokassa merchant account
2. Go to Settings → Notification URLs
3. Set the following URLs:

**Notification URL (Result):**
```
https://your-railway-url/webhook/robokassa/result
```

**Success URL:**
```
https://your-railway-url/webhook/robokassa/success
```

**Fail URL:**
```
https://your-railway-url/webhook/robokassa/fail
```

Replace `your-railway-url` with the URL from Step 4.

### Step 6: Deploy

1. Railway will automatically deploy when you push to GitHub
2. To manually trigger deployment:
   - Go to your service in Railway
   - Click "Redeploy" button
3. Watch the deployment logs in the "Deployments" tab

### Step 7: Verify Deployment

1. Check the logs to ensure both services started:
   ```
   Starting webhook server on port 5000
   Starting bot...
   ```

2. Test the bot in Telegram:
   - Find your bot and send `/start`
   - Verify it responds with the welcome message

3. Test the webhook:
   ```bash
   curl https://your-railway-url/health
   ```
   Should return: `{"status": "healthy"}`

## Monitoring and Logs

### View Logs

1. In Railway dashboard, go to your service
2. Click "Logs" tab
3. View real-time logs from both bot and webhook server

### Common Issues

**Bot not responding:**
- Check logs for errors
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Ensure bot service is running

**Webhook not receiving payments:**
- Check logs for webhook errors
- Verify Robokassa notification URL is correct
- Test with Robokassa test mode first

**Database errors:**
- SQLite database is stored in container memory
- Data will be lost on container restart
- Consider migrating to PostgreSQL for production

## Upgrading to PostgreSQL

For production deployments with persistent data:

1. In Railway dashboard, add a new service
2. Select "PostgreSQL" from the marketplace
3. Railway will automatically set `DATABASE_URL` environment variable
4. Update `database.py` to use PostgreSQL instead of SQLite

See `DEPLOYMENT.md` for PostgreSQL migration guide.

## Scaling

Railway automatically handles scaling:

- **Vertical Scaling:** Increase RAM/CPU in service settings
- **Horizontal Scaling:** Add more replicas (for webhook server)
- **Load Balancing:** Railway handles automatically

## Cost Estimation

**Free Tier:**
- 512MB RAM
- 100GB bandwidth/month
- Enough for small to medium deployments

**Paid Plans:**
- $5/month for additional resources
- Pay-as-you-go for additional bandwidth

## Backup and Recovery

### Database Backup

Since SQLite is stored in the container:

1. **Option 1:** Migrate to PostgreSQL (recommended)
2. **Option 2:** Use Railway's snapshot feature
3. **Option 3:** Implement backup script to S3

### Recovery

1. If deployment fails, Railway keeps previous versions
2. Click "Rollback" in Deployments tab to revert to previous version
3. Check logs to diagnose issues

## Advanced Configuration

### Custom Domain

1. In Railway dashboard, go to service settings
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as instructed
5. Update Robokassa webhook URLs with custom domain

### Environment-Specific Variables

Create different Railway projects for:
- **Development:** `ROBOKASSA_TEST_MODE=True`
- **Production:** `ROBOKASSA_TEST_MODE=False`

### CI/CD Pipeline

Railway automatically deploys on GitHub push. To customize:

1. Go to service settings
2. Click "Build & Deploy"
3. Configure build triggers and deployment rules

## Troubleshooting

### Deployment Failed

1. Check "Deployments" tab for error logs
2. Verify all environment variables are set
3. Ensure `Dockerfile` is in the root directory
4. Check that `requirements.txt` has all dependencies

### Bot Crashes

1. View logs in "Logs" tab
2. Check for Python errors
3. Verify API keys are valid
4. Ensure database permissions are correct

### High Memory Usage

1. Reduce `max_tokens` in OpenAI API calls
2. Implement message history cleanup
3. Upgrade to higher tier service
4. Monitor with Railway's metrics dashboard

## Monitoring and Alerts

### Set Up Alerts

1. In Railway dashboard, go to "Alerts"
2. Create alerts for:
   - High CPU usage
   - High memory usage
   - Service crashes
   - Failed deployments

### Metrics

View real-time metrics:
- CPU usage
- Memory usage
- Network I/O
- Request count

## Updating the Bot

To update the bot code:

1. Make changes to your GitHub repository
2. Commit and push to main branch
3. Railway automatically detects changes
4. Deployment starts automatically
5. Monitor in "Deployments" tab

## Security Best Practices

1. **Never commit .env file** - Use Railway's environment variables
2. **Use strong passwords** - For Robokassa and other services
3. **Enable HTTPS** - Railway provides automatic SSL
4. **Rotate API keys** - Regularly update credentials
5. **Monitor logs** - Watch for suspicious activity
6. **Use private repository** - If containing sensitive data

## Performance Optimization

### Reduce Cold Start Time

1. Minimize dependencies in `requirements.txt`
2. Use lightweight Python base image (already done)
3. Pre-compile Python modules

### Optimize Database

1. Add indexes to frequently queried columns
2. Archive old messages periodically
3. Consider PostgreSQL for better performance

### Reduce API Calls

1. Implement caching for OpenAI responses
2. Batch process messages
3. Use lower token limits for responses

## Support and Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Community:** https://railway.app/community
- **GitHub Issues:** Report issues in your repository

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure Robokassa webhooks
3. ✅ Test bot functionality
4. ✅ Monitor logs and metrics
5. ✅ Set up alerts
6. ✅ Plan for scaling

---

**Your bot is now live on Railway! 🚀**

For questions or issues, check the logs and refer to the troubleshooting section above.
