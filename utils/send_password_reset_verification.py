from django.conf import settings
from utils.send_email import send_email_custom
import logging

logger = logging.getLogger(__name__)


def send_password_reset_verification(user):
    """Send 6-digit verification code to user's email for password reset"""
    from accounts.models import VerificationCode  
    
    # Generate 6-digit code
    code = VerificationCode.generate_code()
    
    # Invalidate any existing password reset codes for this user
    VerificationCode.objects.filter(
        user=user,
        label=VerificationCode.RESET_PASSWORD,
        is_verified=False
    ).update(is_verified=True)  
    
    # Create new verification code record
    VerificationCode.objects.create(
        user=user,
        email=user.email,
        code=code,
        label=VerificationCode.RESET_PASSWORD
    )
    
    # Prepare email context
    context = {
        "full_name": user.full_name,
        "reset_code": code,
        "company_name": settings.COMPANY_NAME,
        "company_logo_url": settings.COMPANY_LOGO_URL,
        "youtube": settings.YOUTUBE,
        "instagram": settings.INSTAGRAM,
        "twitter": settings.TWITTER,
        "tiktok": settings.TIKTOK,
        "youtube_icon_url": settings.YOUTUBE_ICON_URL,
        "instagram_icon_url": settings.INSTAGRAM_ICON_URL,
        "twitter_icon_url": settings.TWITTER_ICON_URL,
        "tiktok_icon_url": settings.TIKTOK_ICON_URL,
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_minutes": getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 10),
    }

    send_email_custom(
        recipient=user.email,
        subject="Reset Your Password",
        template="emails/password_reset_verification.html",
        context=context,
    )
    
    logger.info(f"Password reset code sent to {user.email}")
    return code

