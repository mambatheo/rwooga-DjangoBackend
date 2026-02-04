import logging
import threading
from typing import Dict, Any
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _send_email_thread(recipient, subject, html_content, text_content):
    """Runs in background thread — actually sends the email"""
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        result = email.send(fail_silently=False)

        if result:
            logger.info(f"Email sent successfully to {recipient}: {subject}")
        else:
            logger.warning(f"Email send returned 0 for {recipient}: {subject}")

    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {subject}. Error: {str(e)}")


def send_email_custom(
    recipient: str,
    subject: str,
    template: str,
    context: Dict[str, Any]
) -> bool:
    """
    Send a custom HTML email in a background thread.
    Template rendering happens here (main thread),
    actual SMTP sending happens in background.
    """
    try:
        # Render template in main thread (fast, no I/O)
        html_content = render_to_string(template, context)
        text_content = strip_tags(html_content)

        # Send email in background thread (slow SMTP I/O)
        thread = threading.Thread(
            target=_send_email_thread,
            args=(recipient, subject, html_content, text_content),
            daemon=True
        )
        thread.start()

        return True

    except Exception as e:
        logger.error(f"Failed to prepare email to {recipient}: {subject}. Error: {str(e)}")
        raise