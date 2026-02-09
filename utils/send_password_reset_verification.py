from django.conf import settings
from django.core.signing import TimestampSigner
from utils.send_email import send_email_custom


def send_password_reset_verification(user):    
    # Create signed token containing user ID
    signer = TimestampSigner(salt='password-reset')
    token = signer.sign(str(user.id))    
    # Build password reset URL with signed token (HashRouter format)
    reset_url = f"{settings.SITE_URL}/#/reset-password?token={token}"

    context = {
        "full_name": user.full_name,
        "reset_password_link": reset_url,         
        "company_name": settings.COMPANY_NAME,
        "company_url":settings.COMPANY_URL,
        "company_logo_url": settings.COMPANY_LOGO_URL,
        "youtube": settings.YOUTUBE,
        "instagram": settings.INSTAGRAM,
        "linkdin": settings.LINKDIN,
        "twitter": settings.TWITTER,
        "tiktok": settings.TIKTOK,
        "youtube_icon_url": settings.YOUTUBE_ICON_URL,
        "instagram_icon_url": settings.INSTAGRAM_ICON_URL,
        "twitter_icon_url": settings.TWITTER_ICON_URL,
        "tiktok_icon_url": settings.TIKTOK_ICON_URL,
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_minutes": getattr(settings, 'PASSWORD_RESET_EXPIRY_MINUTES', 30),  
    }

    send_email_custom(
        recipient=user.email,
        subject="Reset Your Password",
        template="emails/password_reset_verification.html",
        context=context,
    )

    return token