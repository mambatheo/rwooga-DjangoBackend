from django.conf import settings
from utils.send_email import send_email_custom
import logging

logger = logging.getLogger(__name__)


def send_registration_verification(user):
    """Send 6-digit verification code to user's email for registration"""
    from accounts.models import VerificationCode  # Import here to avoid circular import
    
    # Generate 6-digit code
    code = VerificationCode.generate_code()
    
    # Invalidate any existing registration verification codes for this user
    VerificationCode.objects.filter(
        user=user,
        label=VerificationCode.REGISTER,
        is_verified=False
    ).update(is_verified=True)  # Mark old codes as used
    
    # Create new verification code record
    VerificationCode.objects.create(
        user=user,
        email=user.email,
        code=code,
        label=VerificationCode.REGISTER
    )
    
    # Prepare email context
    context = {
        "full_name": user.full_name,
        "verification_code": code,
        "company_name": settings.COMPANY_NAME,
        "company_logo_url": settings.COMPANY_LOGO_URL,
        "youtube_icon_url": settings.YOUTUBE_ICON_URL,
        "instagram_icon_url": settings.INSTAGRAM_ICON_URL,
        "twitter_icon_url": settings.TWITTER_ICON_URL,
        "tiktok_icon_url": settings.TIKTOK_ICON_URL,
        "youtube_url": settings.YOUTUBE,
        "instagram_url": settings.INSTAGRAM,
        "twitter_url": settings.TWITTER,
        "tiktok_url": settings.TIKTOK,
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_minutes": getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 10),
    }

    send_email_custom(
        recipient=user.email,
        subject="Verify Your Email",
        template="emails/registration_verification.html",
        context=context,
    )
    
    logger.info(f"Verification code sent to {user.email}")
    return code

