# Vercel Deployment Guide - Wise Guide Bot

**⚠️ Important Note:** Vercel is primarily designed for serverless functions and static sites. While it can host the webhook server, **the Telegram bot polling cannot run on Vercel** because it requires a continuously running process.

## Recommended Approach

For the best experience, use:
- **Railway** for the Telegram bot (long-running process)
- **Vercel** for the webhook server (serverless function)

Or simply use **Railway for everything** (simpler setup).

## Option 1: Railway + Vercel (Hybrid)

### Architecture

```
┌─────────────────────────────────────────┐
│         Telegram Users                  │
└──────────────┬──────────────────────────┘
               │
       ┌───────▼────────┐
       │  Telegram API  │
       └───────┬────────┘
               │
       ┌───────▼────────────────┐
       │  Railway (Bot Service) │  ← Long-running bot process
       │  - bot.py              │
       └───────┬────────────────┘
               │
       ┌───────▼────────────────┐
       │ Robokassa Payment      │
       │ Notification           │
       └───────┬────────────────┘
               │
       ┌───────▼────────────────┐
       │ Vercel (Webhook)       │  ← Serverless webhook
       │ - /webhook/robokassa/* │
       └────────────────────────┘
```

### Setup Steps

#### Part 1: Deploy Bot to Railway

Follow the `RAILWAY_DEPLOYMENT.md` guide to deploy the bot.

#### Part 2: Deploy Webhook to Vercel

1. **Create Vercel project:**
   - Go to https://vercel.com
   - Click "New Project"
   - Import your GitHub repository

2. **Create Vercel API routes:**
   - Create `/api/webhook/robokassa/result.py`
   - Create `/api/webhook/robokassa/success.py`
   - Create `/api/webhook/robokassa/fail.py`

3. **Set environment variables in Vercel:**
   - Go to project settings
   - Add the same environment variables as Railway

4. **Update Robokassa URLs:**
   ```
   https://your-vercel-project.vercel.app/api/webhook/robokassa/result
   https://your-vercel-project.vercel.app/api/webhook/robokassa/success
   https://your-vercel-project.vercel.app/api/webhook/robokassa/fail
   ```

## Option 2: Railway Only (Recommended)

**This is the simplest and most reliable approach.**

Simply follow `RAILWAY_DEPLOYMENT.md` - Railway handles both the bot and webhook server perfectly.

## Option 3: Vercel Only (Not Recommended)

If you still want to use Vercel only, you would need to:

1. Convert the bot to use Telegram Webhooks instead of polling
2. Implement all services as serverless functions
3. Use an external service like AWS Lambda for the long-running bot

This is complex and not recommended. **Use Railway instead.**

## Vercel Webhook Implementation (If Needed)

If you want to run the webhook on Vercel, here's how:

### Create Vercel API Routes

Create `/api/webhook/robokassa/result.py`:

```python
from http.server import BaseHTTPRequestHandler
import hashlib
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import Database
from robokassa_handler import RobokassaHandler

db = Database()
robokassa = RobokassaHandler(
    login=os.getenv("ROBOKASSA_LOGIN"),
    password1=os.getenv("ROBOKASSA_PASSWORD1"),
    password2=os.getenv("ROBOKASSA_PASSWORD2"),
    price=float(os.getenv("SUBSCRIPTION_PRICE", "500")),
    test_mode=os.getenv("ROBOKASSA_TEST_MODE", "True").lower() == "true"
)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse form data
            params = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    params[key] = value
            
            merchant_login = params.get('MerchantLogin')
            sum_ = float(params.get('Sum', 0))
            inv_id = int(params.get('InvId', 0))
            signature = params.get('SignatureValue', '')
            
            # Verify and process
            if merchant_login != robokassa.login:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid merchant")
                return
            
            if not robokassa.verify_payment(sum_, inv_id, signature):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid signature")
                return
            
            if db.complete_payment(str(inv_id), 30):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error")
        
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error")
```

Create `/api/webhook/robokassa/success.py`:

```python
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        inv_id = self.path.split('?InvId=')[-1] if '?InvId=' in self.path else None
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "success",
            "message": "Спасибо за оплату! Ваша подписка активирована.",
            "inv_id": inv_id
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.do_GET()
```

Create `/api/webhook/robokassa/fail.py`:

```python
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        inv_id = self.path.split('?InvId=')[-1] if '?InvId=' in self.path else None
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "failed",
            "message": "Платёж не был завершён. Пожалуйста, попробуйте снова.",
            "inv_id": inv_id
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.do_GET()
```

### Issues with Vercel-Only Approach

1. **Bot won't work** - Vercel terminates functions after 10 seconds
2. **Database persistence** - SQLite won't persist between function calls
3. **Complex setup** - Requires significant refactoring
4. **Higher costs** - Webhook calls add up quickly

## Comparison Table

| Feature | Railway | Vercel | Vercel + Railway |
|---------|---------|--------|------------------|
| Bot polling | ✅ Yes | ❌ No | ✅ Yes |
| Webhook | ✅ Yes | ✅ Yes | ✅ Yes |
| Database | ✅ SQLite/PostgreSQL | ⚠️ Requires external DB | ✅ Yes |
| Cost | $5-20/month | $0-20/month | $5-20/month |
| Complexity | Low | High | Medium |
| Recommended | ⭐⭐⭐ | ❌ | ⭐⭐ |

## Final Recommendation

**Use Railway for everything.** It's:
- ✅ Simpler to set up
- ✅ More reliable
- ✅ Better for long-running processes
- ✅ Cheaper than Vercel for this use case
- ✅ Built for exactly this type of application

Follow `RAILWAY_DEPLOYMENT.md` for the best experience.

---

**If you still want to use Vercel, use the Railway + Vercel hybrid approach.**
