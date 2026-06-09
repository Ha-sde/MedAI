import os
from twilio.rest import Client

def format_phone_number(phone):
    """Format phone number to E.164 if not already formatted."""
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if not cleaned.startswith('+'):
        # If it's a 10-digit number, assume Indian country code (+91) as default
        if len(cleaned) == 10:
            return f"+91{cleaned}"
        elif len(cleaned) > 10 and cleaned.startswith('91'):
            return f"+{cleaned}"
    return cleaned

def send_otp_sms(phone, otp):
    """Send SMS message containing the 6-digit OTP using the Twilio API."""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_phone = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not account_sid or not auth_token or not from_phone:
        print("[SMS] Twilio credentials not fully set. Falling back to Demo Mode.")
        return False
        
    formatted_phone = format_phone_number(phone)
    body = f"Your MedAI verification code is: {otp}. Valid for 10 minutes."
    
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_phone,
            to=formatted_phone
        )
        print(f"[SMS] Sent OTP successfully to {formatted_phone}. Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"[Twilio Error] Failed to send SMS to {formatted_phone}: {e}")
        return False
