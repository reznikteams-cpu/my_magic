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
    PAYMENT_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"
    
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
    
    def generate_payment_link(self, user_id: int, description: str, subscription_id: Optional[int] = None) -> str:
        """
        Generate a payment link for Robokassa according to official documentation.
        
        IMPORTANT: According to Robokassa docs, the signature is calculated as:
        MerchantLogin:OutSum::Password#1
        
        Note the double colon (::) - InvId is included in signature calculation but with EMPTY value.
        InvId is NOT included in the URL parameters.
        
        Args:
            user_id: Telegram user ID (used for tracking, not in URL)
            description: Payment description
            subscription_id: Optional subscription ID (not used in simple payment)
        
        Returns:
            Payment link URL
        """
        try:
            # Generate signature (MD5 hash)
            # CORRECT FORMAT: MerchantLogin:OutSum::Password#1
            # Note: InvId is represented by empty value between colons
            signature_string = f"{self.login}:{self.price}::{self.password1}"
            signature = hashlib.md5(signature_string.encode()).hexdigest()
            
            # Build payment link parameters
            # According to docs, only these 4 parameters are used:
            # MerchantLogin, OutSum, Description, SignatureValue
            params = {
                "MerchantLogin": self.login,
                "OutSum": str(self.price),
                "Description": description,
                "SignatureValue": signature,
            }
            
            # Generate full URL
            payment_link = f"{self.PAYMENT_URL}?{urlencode(params)}"
            logger.info(f"Payment link generated for user {user_id}")
            logger.debug(f"Signature string: {signature_string}")
            logger.debug(f"Signature: {signature}")
            return payment_link
        
        except Exception as e:
            logger.error(f"Error generating payment link: {e}")
            return ""
    
    def verify_payment(self, out_sum: float, inv_id: int, signature: str, custom_params: Optional[dict] = None) -> bool:
        """
        Verify payment signature from Robokassa webhook.
        
        According to Robokassa docs, webhook signature is calculated as:
        MD5(OutSum:InvId:Password#2) or with custom params:
        MD5(OutSum:InvId:Password#2:Shp_param1=value1:Shp_param2=value2...)
        
        Note: Here InvId HAS a value (unlike in payment link generation).
        
        Args:
            out_sum: Payment amount
            inv_id: Invoice ID (user_id)
            signature: Signature from Robokassa
            custom_params: Optional custom parameters dict
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate expected signature
            # Format: OutSum:InvId:Password#2 (with actual InvId value)
            signature_string = f"{out_sum}:{inv_id}:{self.password2}"
            
            # Add custom parameters if provided (sorted by key)
            if custom_params:
                for key in sorted(custom_params.keys()):
                    if key.startswith("Shp_"):
                        signature_string += f":{key}={custom_params[key]}"
            
            expected_signature = hashlib.md5(signature_string.encode()).hexdigest()
            
            # Compare signatures (case-insensitive)
            is_valid = signature.lower() == expected_signature.lower()
            
            if is_valid:
                logger.info(f"Payment verified for invoice {inv_id}")
            else:
                logger.warning(f"Payment signature mismatch for invoice {inv_id}")
                logger.debug(f"Expected: {expected_signature}, Got: {signature}")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    def get_webhook_response(self, inv_id: int) -> str:
        """
        Generate proper webhook response for Robokassa.
        
        According to Robokassa docs, the response should be:
        - "OK" for successful verification
        - "OK{InvId}" format is also acceptable
        
        Args:
            inv_id: Invoice ID
        
        Returns:
            Response string
        """
        return f"OK{inv_id}"
    
    def generate_payment_form_link(self, user_id: int, description: str, subscription_id: Optional[int] = None) -> str:
        """
        Generate a direct payment form link using Robokassa iframe endpoint.
        This method works directly in Telegram without requiring JavaScript execution.
        
        Uses the FormMS.if iframe endpoint from Robokassa.
        
        IMPORTANT: Same rules apply as generate_payment_link - signature uses empty InvId.
        
        Args:
            user_id: Telegram user ID (for tracking, not in URL)
            description: Payment description
            subscription_id: Optional subscription ID (not used in simple payment)
        
        Returns:
            Direct payment form URL
        """
        try:
            # Generate signature (MD5 hash)
            # CORRECT FORMAT: MerchantLogin:OutSum::Password#1
            signature_string = f"{self.login}:{self.price}::{self.password1}"
            signature = hashlib.md5(signature_string.encode()).hexdigest()
            
            # Build parameters for direct iframe
            params = {
                "MerchantLogin": self.login,
                "OutSum": str(self.price),
                "Description": description,
                "SignatureValue": signature,
            }
            
            # Use FormMS.if - direct iframe endpoint
            # This endpoint returns an iframe that can be opened directly in browser
            form_url = f"https://auth.robokassa.ru/Merchant/PaymentForm/FormMS.if?{urlencode(params)}"
            
            logger.info(f"Payment form link generated for user {user_id}")
            logger.debug(f"Signature string: {signature_string}")
            logger.debug(f"Signature: {signature}")
            return form_url
        
        except Exception as e:
            logger.error(f"Error generating payment form link: {e}")
            return ""
