"""
Flask webhook server for handling Robokassa payment notifications.
"""

import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

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

# Initialize Flask app
app = Flask(__name__)

# Initialize database
db = Database()

# Initialize Robokassa handler
robokassa = RobokassaHandler(
    login=os.getenv("ROBOKASSA_LOGIN", "YOUR_ROBOKASSA_LOGIN"),
    password1=os.getenv("ROBOKASSA_PASSWORD1", "YOUR_ROBOKASSA_PASSWORD1"),
    password2=os.getenv("ROBOKASSA_PASSWORD2", "YOUR_ROBOKASSA_PASSWORD2"),
    price=float(os.getenv("SUBSCRIPTION_PRICE", "500")),
    test_mode=os.getenv("ROBOKASSA_TEST_MODE", "True").lower() == "true"
)

SUBSCRIPTION_DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))


@app.route('/webhook/robokassa/result', methods=['POST'])
def robokassa_result():
    """
    Handle Robokassa payment result notification.
    
    Expected POST parameters:
    - MerchantLogin: Merchant login
    - Sum: Payment amount
    - InvId: Invoice ID (user_id)
    - SignatureValue: MD5 signature
    """
    try:
        merchant_login = request.form.get('MerchantLogin')
        sum_ = float(request.form.get('Sum', 0))
        inv_id = int(request.form.get('InvId', 0))
        signature = request.form.get('SignatureValue', '')
        
        logger.info(f"Received Robokassa notification: merchant={merchant_login}, sum={sum_}, inv_id={inv_id}")
        
        # Verify merchant login
        if merchant_login != robokassa.login:
            logger.error(f"Invalid merchant login: {merchant_login}")
            return "Invalid merchant", 400
        
        # Verify payment signature
        if not robokassa.verify_payment(sum_, inv_id, signature):
            logger.error(f"Invalid signature for invoice {inv_id}")
            return "Invalid signature", 400
        
        # Complete payment and activate subscription
        if db.complete_payment(str(inv_id), SUBSCRIPTION_DAYS):
            logger.info(f"Subscription activated for user {inv_id}")
            return "OK", 200
        else:
            logger.error(f"Failed to complete payment for user {inv_id}")
            return "Payment processing error", 500
    
    except Exception as e:
        logger.error(f"Error processing Robokassa result: {e}")
        return "Error", 500


@app.route('/webhook/robokassa/success', methods=['GET', 'POST'])
def robokassa_success():
    """
    Handle successful payment redirect from Robokassa.
    User is redirected here after successful payment.
    """
    try:
        inv_id = request.args.get('InvId') or request.form.get('InvId')
        logger.info(f"Payment success redirect for invoice {inv_id}")
        
        return jsonify({
            "status": "success",
            "message": "Спасибо за оплату! Ваша подписка активирована. Вернитесь в Telegram бота.",
            "inv_id": inv_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing success redirect: {e}")
        return jsonify({"status": "error", "message": "Error processing payment"}), 500


@app.route('/webhook/robokassa/fail', methods=['GET', 'POST'])
def robokassa_fail():
    """
    Handle failed payment redirect from Robokassa.
    User is redirected here if payment was cancelled or failed.
    """
    try:
        inv_id = request.args.get('InvId') or request.form.get('InvId')
        logger.warning(f"Payment failed for invoice {inv_id}")
        
        return jsonify({
            "status": "failed",
            "message": "Платёж не был завершён. Пожалуйста, попробуйте снова.",
            "inv_id": inv_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing fail redirect: {e}")
        return jsonify({"status": "error", "message": "Error processing payment"}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint."""
    return jsonify({
        "name": "Wise Guide Bot - Webhook Server",
        "version": "1.0.0",
        "status": "running"
    }), 200


if __name__ == '__main__':
    port = int(os.getenv("WEBHOOK_PORT", "5000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
