# TELEGRAM LOGIN - utils/telegram_verify.py
import hmac
import hashlib
import time

def verify_telegram_hash(data: dict, bot_token: str) -> bool:
    """
    Verify the hash of the data received from Telegram OAuth.
    See: https://core.telegram.org/widgets/login#checking-authorization
    """
    if 'hash' not in data:
        return False
    
    received_hash = data.pop('hash')
    
    # Sort keys alphabetically and join them as key=value pairs separated by newlines
    sorted_keys = sorted(data.keys())
    check_string = "\n".join([f"{k}={data[k]}" for k in sorted_keys if data[k] is not None])
    
    # Secret key is SHA256 of the bot token
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    
    # Compute HMAC-SHA256 of the check string using the secret key
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    
    # Check if the hashes match
    if computed_hash != received_hash:
        return False
    
    # Check if auth_date is within 24 hours (86400 seconds)
    auth_date = int(data.get('auth_date', 0))
    current_time = int(time.time())
    if current_time - auth_date > 86400:
        return False
    
    return True
