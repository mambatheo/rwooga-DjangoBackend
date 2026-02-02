from django.conf import settings
from utils.send_email import send_email_custom


def send_password_reset_verification(user):
   
    from accounts.models import VerificationCode

    verification = VerificationCode.objects.create(
        user=user,
        email=user.email,
        label=VerificationCode.RESET_PASSWORD
    )

    reset_url = (
        f"{settings.SITE_URL}"
        f"/reset-password?token={verification.token}"
    )

    context = {
        "full_name": user.full_name,
        "reset_password_link": reset_url, 
        "company_name": settings.COMPANY_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_minutes": settings.VERIFICATION_CODE_EXPIRY_MINUTES,
    }

    send_email_custom(
        recipient=user.email,
        subject="Reset Your Password",
        template="emails/password_reset_verification.html",
        context=context,
    )

    return verification