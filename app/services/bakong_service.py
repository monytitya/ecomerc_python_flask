from bakong_khqr import KHQR
import os
from dotenv import load_dotenv

load_dotenv()

khqr = KHQR(os.getenv("BAKONG_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiZTFhMjA5NmUxZWE2NGMzYiJ9LCJpYXQiOjE3Nzk0NjM2MjYsImV4cCI6MTc4NzIzOTYyNn0.yYeUa6uKax99mSiKBCwjpxR75S9KVqLk76A_KH_Cd8A"))


def generate_qr(
    amount: float,
    currency: str,
    bill_number: str,
    store_label: str,
    phone_number: str
) -> str:
    """
    Generate a Bakong KHQR payment QR code string.
    
    Args:
        amount: Payment amount (supports decimals for USD)
        currency: Currency code - 'USD' or 'KHR'
        bill_number: Unique bill/invoice number
        store_label: Label for the store/merchant
        phone_number: Customer phone number (e.g. '85512345678')
    
    Returns:
        EMVCo-compliant QR code string
    """
    qr_string = khqr.create_qr(
        bank_account=os.getenv("BAKONG_ACCOUNT", "mao_tityamony@bkrt"),
        merchant_name=os.getenv("MERCHANT_NAME", "Ecomerc shop"),
        merchant_city=os.getenv("MERCHANT_CITY", "Phnom Penh"),
        amount=amount,
        currency=currency,
        store_label=store_label,
        phone_number=phone_number,
        bill_number=bill_number,
        terminal_label="POS-01",
        static=True     # Dynamic QR (unique per transaction)
        
    )
    return qr_string


def generate_deeplink(qr_string: str, callback_url: str = "https://bakong-deeplink.nbc.gov.kh/bakong/GGohjnA7BxI95v5zi") -> str:
    """
    Generate a Bakong mobile app deeplink from a QR string.
    
    Args:
        qr_string: The EMVCo QR code string
        callback_url: URL to redirect after payment
    
    Returns:
        Deeplink URL string for the Bakong mobile app
    """
    return khqr.generate_deeplink(
        qr_string,
        callback=callback_url,
        appIconUrl="https://yourshop.com/logo.png",
        appName="Ecomerc Shop"
    )


def check_payment_status(md5: str):
    """
    Check whether a payment has been completed.
    
    Args:
        md5: MD5 hash of the QR string (used as transaction ID)
    
    Returns:
        Payment status result from Bakong API, or None if unpaid
    """
    return khqr.check_payment(md5)


def get_payment_info(md5: str):
    """
    Get detailed payment information.
    
    Args:
        md5: MD5 hash of the QR string
    
    Returns:
        Detailed payment info dict, or None if not found
    """
    return khqr.get_payment(md5)
