"""
Email sending utilities for the application.

Provides functions to send HTML emails with proper error handling and logging.
"""

import logging
from typing import Dict, Any

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


def send_email_custom(
    recipient: str, 
    subject: str, 
    template: str, 
    context: Dict[str, Any]
) -> bool:
    """
    Send a custom HTML email to a recipient.
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject line
        template: Path to the HTML email template (relative to templates directory)
        context: Dictionary of context variables for the template
        
    Returns:
        True if email was sent successfully, False otherwise
        
    Raises:
        Exception: If there's a critical error in email configuration
    """
    try:
        # Render HTML content from template
        html_content = render_to_string(template, context)
        text_content = strip_tags(html_content)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        result = email.send(fail_silently=False)
        
        if result:
            logger.info(f"Email sent successfully to {recipient}: {subject}")
            return True
        else:
            logger.warning(f"Email send returned 0 for {recipient}: {subject}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {subject}. Error: {str(e)}")
        raise
