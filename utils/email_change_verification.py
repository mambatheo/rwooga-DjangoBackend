from django.conf import settings
from django.utils import timezone
from utils.send_email import send_email_custom
import logging

logger = logging.getLogger(__name__)


def send_email_change_verification(user, new_email):

    from accounts.models import VerificationCode  
    
    # Generate 6-digit code
    code = VerificationCode.generate_code()
    
    # Invalidate any existing email change codes for this user
    VerificationCode.objects.filter(
        user=user,
        label=VerificationCode.EMAIL_CHANGE,
        is_verified=False
    ).update(is_verified=True)  
    
    # Create new verification code record
    # Note: email field stores the NEW email, not the current one
    VerificationCode.objects.create(
        user=user,
        email=new_email,
        code=code,
        label=VerificationCode.EMAIL_CHANGE
    )
    
    context = {
        "full_name": user.full_name,
        "current_email": user.email,
        "new_email": new_email,
        "verification_code": code, 
        "company_name": settings.COMPANY_NAME,
        "company_logo_url": settings.COMPANY_LOGO_URL,
        "company_url": settings.COMPANY_URL,  
        
        # Social media links 
        "youtube": settings.YOUTUBE,
        "instagram": settings.INSTAGRAM,
        "twitter": settings.TWITTER,
        "tiktok": settings.TIKTOK,
        "linkedin": settings.LINKEDIN,  
        
        # Social media icon URLs
        "youtube_icon_url": settings.YOUTUBE_ICON_URL,
        "instagram_icon_url": settings.INSTAGRAM_ICON_URL,
        "twitter_icon_url": settings.TWITTER_ICON_URL,
        "tiktok_icon_url": settings.TIKTOK_ICON_URL,
        "linkedin_icon_url": settings.LINKEDIN_ICON_URL,  
        
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_minutes": settings.VERIFICATION_CODE_EXPIRY_MINUTES, 
        "current_year": timezone.now().year,  
    }

    # Send to NEW email address (not current one)
    send_email_custom(
        recipient=new_email,
        subject="Verify Your New Email Address",
        template="emails/email_change_verification.html",
        context=context,
    )
    
    logger.info(f"Email change verification code sent to {new_email} for user {user.id}")
    return code