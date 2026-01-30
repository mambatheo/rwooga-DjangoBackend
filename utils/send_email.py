from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives


def send_email_custom(recipient, subject: str, template: str, context: dict):
   
    html_content = render_to_string(template, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.EMAIL_HOST_USER,
        [recipient],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
