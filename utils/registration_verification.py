from django.conf import settings
from django.core.signing import TimestampSigner
from utils.send_email import send_email_custom


def send_registration_verification(user):   
    # Create signed token containing user ID
    signer = TimestampSigner(salt='email-verification')
    token = signer.sign(str(user.id))
    
    # Build verification URL with signed token (HashRouter format)
    verify_url = f"{settings.SITE_URL}/#/verify-email?token={token}"

    context = {
        "full_name": user.full_name,
        "verification_link": verify_url,
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
        "expiry_minutes": getattr(settings, 'EMAIL_VERIFICATION_EXPIRY_MINUTES', 30), 
    }

    send_email_custom(
        recipient=user.email,
        subject="Verify Your Email",
        template="emails/registration_verification.html",
        context=context,
    )

    return token