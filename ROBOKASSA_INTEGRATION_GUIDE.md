# Robokassa Integration Guide

## Overview

This guide explains how the Wise Guide Bot integrates with Robokassa for subscription payments. The integration has been updated to follow the official Robokassa API documentation.

## Key Changes Made

### 1. Correct API Endpoints

**Before:** Used incorrect test endpoints  
**After:** Uses official Robokassa payment interface:
```
https://auth.robokassa.ru/Merchant/Index.aspx
```

### 2. Correct Parameter Names

**Before:** Used `Sum` parameter  
**After:** Uses official `OutSum` parameter (as per Robokassa docs)

| Parameter | Description | Example |
|-----------|-------------|---------|
| MerchantLogin | Your merchant ID | demo |
| OutSum | Payment amount (not Sum!) | 500.00 |
| InvId | Unique invoice ID | 123456789 |
| Description | Payment description | Подписка на 30 дней |
| SignatureValue | MD5 hash | a1b2c3d4e5f6... |

### 3. Correct Signature Calculation

**Payment Link Signature:**
```
MD5(MerchantLogin:OutSum:InvId:Password#1)
```

**Webhook Verification Signature:**
```
MD5(OutSum:InvId:Password#2)
```

With custom parameters:
```
MD5(OutSum:InvId:Password#2:Shp_user_id=123:Shp_subscription_id=456)
```

### 4. Custom Parameters Support

The bot now supports custom parameters for tracking:
```python
params = {
    "Shp_user_id": str(user_id),
    "Shp_subscription_id": str(subscription_id),
}
```

These parameters are included in the signature calculation for security.

### 5. Webhook Response Format

**Before:** Returned generic "OK"  
**After:** Returns proper format as per Robokassa docs:
```python
return f"OK{inv_id}"  # e.g., "OK123456789"
```

## Payment Flow

### 1. User Initiates Payment

```
User clicks "🌙 Подписаться" button in Telegram
↓
Bot generates payment link with signature
↓
User clicks "💳 Оплатить через Robokassa"
```

### 2. Payment Processing

```
User selects payment method on Robokassa
↓
Robokassa processes payment
↓
Robokassa sends POST to ResultURL webhook
↓
Bot verifies signature
↓
Bot activates subscription
↓
User is redirected to SuccessURL
```

### 3. Webhook Verification

The webhook handler (`/webhook/robokassa/result`) performs these checks:

1. **Verify Merchant Login**
   ```python
   if merchant_login != robokassa.login:
       return "Invalid merchant", 400
   ```

2. **Collect Custom Parameters**
   ```python
   custom_params = {}
   for key, value in request.form.items():
       if key.startswith('Shp_'):
           custom_params[key] = value
   ```

3. **Verify Signature**
   ```python
   if not robokassa.verify_payment(out_sum, inv_id, signature, custom_params):
       return "Invalid signature", 400
   ```

4. **Verify Amount**
   ```python
   if out_sum != robokassa.price:
       logger.warning(f"Amount mismatch: expected {robokassa.price}, got {out_sum}")
   ```

5. **Activate Subscription**
   ```python
   if db.complete_payment(str(inv_id), SUBSCRIPTION_DAYS):
       return robokassa.get_webhook_response(inv_id), 200
   ```

## Environment Variables

Required environment variables in `.env`:

```bash
# Robokassa credentials
ROBOKASSA_LOGIN=your_merchant_login
ROBOKASSA_PASSWORD1=your_password_1
ROBOKASSA_PASSWORD2=your_password_2

# Subscription settings
SUBSCRIPTION_PRICE=500
SUBSCRIPTION_DAYS=30

# Webhook configuration
WEBHOOK_PORT=5000

# Testing
ROBOKASSA_TEST_MODE=True
```

## Testing the Integration

### 1. Test Mode Setup

In `.env`, set:
```bash
ROBOKASSA_TEST_MODE=True
```

This uses the official Robokassa test environment.

### 2. Test Payment Flow

1. Start the bot: `python bot.py`
2. Start webhook server: `python webhook_server.py`
3. Send `/start` to bot
4. Click `/profile` → "🌙 Подписаться"
5. Click "💳 Оплатить через Robokassa"
6. You'll be redirected to Robokassa payment page

### 3. Simulate Webhook

To test webhook handling without actual payment:

```bash
curl -X POST http://localhost:5000/webhook/robokassa/result \
  -d "MerchantLogin=demo" \
  -d "OutSum=500.00" \
  -d "InvId=123456789" \
  -d "SignatureValue=<calculated_hash>" \
  -d "Shp_user_id=123456789"
```

Calculate the hash:
```python
import hashlib
hash = hashlib.md5(b"500.00:123456789:password2").hexdigest()
print(hash)
```

## Robokassa Documentation References

- **Payment Interface:** https://docs.robokassa.ru/pay-interface/
- **Testing Mode:** https://docs.robokassa.ru/testing-mode/
- **Webhook Notifications:** https://docs.robokassa.ru/notifications/
- **Parameter Reference:** https://docs.robokassa.ru/parameters-script/

## Troubleshooting

### Issue: "Invalid signature" error

**Cause:** Signature calculation mismatch  
**Solution:**
1. Verify all credentials in `.env`
2. Check parameter names (use `OutSum`, not `Sum`)
3. Ensure custom parameters are sorted by key
4. Verify password#1 for payment links, password#2 for webhook

### Issue: Payment not activating

**Cause:** Webhook not reaching bot  
**Solution:**
1. Check webhook URL in Robokassa settings
2. Verify `WEBHOOK_PORT` is correct
3. Check firewall/NAT settings
4. Review logs: `docker logs <container_id>`

### Issue: Amount mismatch warning

**Cause:** Subscription price changed after payment initiated  
**Solution:**
1. Keep `SUBSCRIPTION_PRICE` consistent
2. For price changes, create new subscription tier with different InvId range
3. Check Robokassa merchant settings for commission

## Production Deployment

### 1. Disable Test Mode

In `.env`, set:
```bash
ROBOKASSA_TEST_MODE=False
```

### 2. Set Correct Webhook URL

In Robokassa merchant settings, set:
- **ResultURL:** `https://your-domain.com/webhook/robokassa/result`
- **SuccessURL:** `https://your-domain.com/webhook/robokassa/success`
- **FailURL:** `https://your-domain.com/webhook/robokassa/fail`

### 3. Enable HTTPS

Robokassa requires HTTPS for webhook endpoints. Use:
- Let's Encrypt SSL certificates
- Nginx/Apache reverse proxy
- Railway/Vercel HTTPS support

### 4. Monitor Payments

Check database for completed payments:
```sql
SELECT * FROM subscriptions WHERE status = 'active' ORDER BY expires_at DESC;
```

## Code Changes Summary

### `robokassa_handler.py`
- Fixed API endpoints
- Corrected signature calculation
- Added custom parameter support
- Improved webhook response format

### `webhook_server.py`
- Updated parameter names (`OutSum` instead of `Sum`)
- Added custom parameter collection
- Improved signature verification
- Added amount verification

### `bot.py`
- Updated payment link generation
- Added subscription tracking
- Improved error handling

## Security Notes

1. **Never hardcode credentials** - use environment variables
2. **Always verify signatures** - prevents payment fraud
3. **Use HTTPS** - protects data in transit
4. **Validate amounts** - ensures correct payment
5. **Log all transactions** - for audit trail
6. **Rotate passwords** - periodically change Robokassa credentials

## Support

For issues with Robokassa integration:
1. Check official docs: https://docs.robokassa.ru/
2. Review logs in bot and webhook server
3. Test with curl commands
4. Contact Robokassa support: support@robokassa.ru
