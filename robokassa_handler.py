"""
Robokassa payment handler for subscription management.
"""

import hashlib
import logging
from typing import Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class RobokassaHandler:
    """Handler for Robokassa payment integration."""
    
    # Robokassa API endpoints
    TEST_URL = "https://test.robokassa.ru/Auth.aspx"
    PROD_URL = "https://auth.robokassa.ru/Auth.aspx"
    
    def __init__(self, login: str, password1: str, password2: str, price: float, test_mode: bool = True):
        """
        Initialize Robokassa handler.
        
        Args:
            login: Robokassa merchant login
            password1: Robokassa password #1 (for generating links)
            password2: Robokassa password #2 (for verifying payments)
            price: Subscription price in RUB
            test_mode: Use test environment if True
        """
        self.login = login
        self.password1 = password1
        self.password2 = password2
        self.price = price
        self.test_mode = test_mode
        self.base_url = self.TEST_URL if test_mode else self.PROD_URL
    
    def generate_payment_link(self, user_id: int, description: str, currency: str = "RUB") -> str:
        """
        Generate a payment link for Robokassa.
        
        Args:
            user_id: Telegram user ID (used as InvId)
            description: Payment description
            currency: Currency code (default: RUB)
        
        Returns:
            Payment link URL
        """
        try:
            # Generate signature (MD5 hash)
            # Format: MerchantLogin:Sum:InvId:Password1
            signature_string = f"{self.login}:{self.price}:{user_id}:{self.password1}"
            signature = hashlib.md5(signature_string.encode()).hexdigest()
            
            # Build payment link parameters
            params = {
                "MerchantLogin": self.login,
                "Sum": str(self.price),
                "InvId": str(user_id),
                "Description": description,
                "SignatureValue": signature,
                "Culture": "ru",
                "IsTest": "1" if self.test_mode else "0",
            }
            
            # Generate full URL
            payment_link = f"{self.base_url}?{urlencode(params)}"
            logger.info(f"Payment link generated for user {user_id}")
            return payment_link
        
        except Exception as e:
            logger.error(f"Error generating payment link: {e}")
            return ""
    
    def verify_payment(self, sum_: float, inv_id: int, signature: str) -> bool:
        """
        Verify payment signature from Robokassa webhook.
        
        Args:
            sum_: Payment amount
            inv_id: Invoice ID (user_id)
            signature: Signature from Robokassa
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate expected signature
            # Format: Sum:InvId:Password2
            signature_string = f"{sum_}:{inv_id}:{self.password2}"
            expected_signature = hashlib.md5(signature_string.encode()).hexdigest()
            
            # Compare signatures (case-insensitive)
            is_valid = signature.lower() == expected_signature.lower()
            
            if is_valid:
                logger.info(f"Payment verified for invoice {inv_id}")
            else:
                logger.warning(f"Payment signature mismatch for invoice {inv_id}")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    def generate_webhook_signature(self, sum_: float, inv_id: int) -> str:
        """
        Generate signature for webhook response.
        
        Args:
            sum_: Payment amount
            inv_id: Invoice ID
        
        Returns:
            Signature hash
        """
        signature_string = f"{sum_}:{inv_id}:{self.password2}"
        return hashlib.md5(signature_string.encode()).hexdigest()
