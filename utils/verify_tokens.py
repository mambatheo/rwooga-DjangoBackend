
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings


def verify_email_token(token):   
    max_age_minutes = getattr(settings, 'EMAIL_VERIFICATION_EXPIRY_MINUTES', 30)
    max_age_seconds = max_age_minutes * 60  # Convert minutes to seconds
    signer = TimestampSigner(salt='email-verification')
    
    try:
        user_id = signer.unsign(token, max_age=max_age_seconds)
        return True, user_id, None
    except SignatureExpired:
        return False, None, "Verification link has expired"
    except BadSignature:
        return False, None, "Invalid verification link"


def verify_password_reset_token(token):
   
    max_age_minutes = getattr(settings, 'PASSWORD_RESET_EXPIRY_MINUTES', 30)
    max_age_seconds = max_age_minutes * 60  # Convert minutes to seconds
    signer = TimestampSigner(salt='password-reset')
    
    try:
        user_id = signer.unsign(token, max_age=max_age_seconds)
        return True, user_id, None
    except SignatureExpired:
        return False, None, "Password reset link has expired"
    except BadSignature:
        return False, None, "Invalid password reset link"