from django.conf import settings
from utils.send_email import send_email_custom


def send_registration_verification(user):
    from accounts.models import VerificationCode

    verification = VerificationCode.objects.create(
        user=user,
        email=user.email,
        label=VerificationCode.REGISTER
    )

    verify_url = (
        f"{settings.SITE_URL}"
        f"/verify-email?token={verification.token}"
    )

    context = {
        "full_name": user.full_name,
        "verification_link": verify_url,
        "company_name": settings.COMPANY_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_minutes": settings.VERIFICATION_CODE_EXPIRY_MINUTES,
    }

    send_email_custom(
        recipient=user.email,
        subject="Verify Your Email",
        template="emails/registration_verification.html",
        context=context,
    )

    return verification