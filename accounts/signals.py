from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_user_tokens(sender, instance, **kwargs):
   
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        
        # Delete all outstanding tokens for this user
        token_count = OutstandingToken.objects.filter(user=instance).count()
        OutstandingToken.objects.filter(user=instance).delete()
        
        logger.info(f"Deleted {token_count} tokens for user {instance.email}")
    except Exception as e:
        logger.error(f"Error deleting tokens for user {instance.email}: {str(e)}")


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_user_verification_codes(sender, instance, **kwargs):
    
    try:
        from accounts.models import VerificationCode
        
        code_count = VerificationCode.objects.filter(user=instance).count()
        logger.info(f"Will delete {code_count} verification codes for user {instance.email}")
    except Exception as e:
        logger.error(f"Error with verification codes for user {instance.email}: {str(e)}")