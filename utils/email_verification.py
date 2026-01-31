"""
Email verification utilities for user registration and password reset.

This module provides functions to generate and send verification codes,
and to validate those codes with proper expiration handling.
"""

import logging
from typing import Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def send_registration_verification(user):
    """
    Generate and send a registration verification code to a user's email.
    
    Args:
        user: User instance to send verification code to
        
    Returns:
        VerificationCode instance if successful, None if email sending fails
        
    Raises:
        Exception: If there's an error generating or sending the verification code
    """
    from accounts.models import VerificationCode
    from utils.code_generator import random_with_N_digits
    from utils.send_email import send_email_custom
    
    try:
        # Generate 6-digit verification code
        code = random_with_N_digits(6)
        
        # Create verification code record
        verification_code = VerificationCode.objects.create(
            user=user,
            email=user.email,
            code=str(code),
            label=VerificationCode.REGISTER
        )
        
        # Prepare email context
        context = {
            'full_name': user.full_name or user.email,
            'code': code,
            'company_name': getattr(settings, 'COMPANY_NAME', 'Rwooga'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@rwooga.com'),
            'expiry_minutes': getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 15),
        }
        
        # Send email
        send_email_custom(
            recipient=user.email,
            subject='Verify Your Email Address',
            template='emails/registration_verification.html',
            context=context
        )
        
        logger.info(f"Registration verification code sent to {user.email}")
        return verification_code
        
    except Exception as e:
        logger.error(f"Failed to send registration verification to {user.email}: {str(e)}")
        raise


def send_password_reset_verification(email: str):
    """
    Generate and send a password reset verification code to an email address.
    
    Args:
        email: Email address to send the password reset code to
        
    Returns:
        VerificationCode instance if successful, None if user doesn't exist
        
    Raises:
        Exception: If there's an error generating or sending the verification code
    """
    from django.contrib.auth import get_user_model
    from accounts.models import VerificationCode
    from utils.code_generator import random_with_N_digits
    from utils.send_email import send_email_custom
    
    User = get_user_model()
    
    try:
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return None
        
        # Generate 6-digit verification code
        code = random_with_N_digits(6)
        
        # Create verification code record
        verification_code = VerificationCode.objects.create(
            user=user,
            email=email,
            code=str(code),
            label=VerificationCode.RESET_PASSWORD
        )
        
        # Prepare email context
        context = {
            'full_name': user.full_name or user.email,
            'code': code,
            'company_name': getattr(settings, 'COMPANY_NAME', 'Rwooga'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@rwooga.com'),
            'expiry_minutes': getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 15),
        }
        
        # Send email
        send_email_custom(
            recipient=email,
            subject='Password Reset Request',
            template='emails/password_reset_verification.html',
            context=context
        )
        
        logger.info(f"Password reset verification code sent to {email}")
        return verification_code
        
    except Exception as e:
        logger.error(f"Failed to send password reset verification to {email}: {str(e)}")
        raise


def verify_code(email: str, code: str, label: str) -> Tuple[bool, Optional[object], str]:
    """
    Verify a verification code for a given email and label.
    
    Args:
        email: Email address associated with the code
        code: The verification code to validate
        label: The type of verification (REGISTER, RESET_PASSWORD, etc.)
        
    Returns:
        Tuple of (is_valid, verification_code, error_message):
            - is_valid: Boolean indicating if the code is valid
            - verification_code: The VerificationCode instance if found, None otherwise
            - error_message: Error message if invalid, empty string if valid
    """
    from accounts.models import VerificationCode
    
    try:
        # Find the most recent verification code for this email and label
        verification_code = VerificationCode.objects.filter(
            email=email,
            code=code,
            label=label,
            email_verified=False
        ).order_by('-created_on').first()
        
        if not verification_code:
            logger.warning(f"Invalid verification code attempt for {email} with label {label}")
            return False, None, "Invalid verification code. Please check and try again."
        
        # Check if code has expired
        if verification_code.is_expired:
            logger.warning(f"Expired verification code used for {email}")
            return False, verification_code, "Verification code has expired. Please request a new one."
        
        # Check if code is still valid
        if not verification_code.is_valid:
            logger.warning(f"Already used verification code for {email}")
            return False, verification_code, "This verification code has already been used."
        
        logger.info(f"Verification code validated successfully for {email}")
        return True, verification_code, ""
        
    except Exception as e:
        logger.error(f"Error verifying code for {email}: {str(e)}")
        return False, None, "An error occurred while verifying your code. Please try again."


def cleanup_expired_codes() -> int:
    """
    Delete expired verification codes from the database.
    
    This function should be called periodically (e.g., via a cron job or celery task)
    to clean up old verification codes.
    
    Returns:
        Number of codes deleted
    """
    from django.utils import timezone
    from datetime import timedelta
    
    expiry_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 15)
    cutoff_time = timezone.now() - timedelta(minutes=expiry_minutes)
    
    deleted_count, _ = VerificationCode.objects.filter(
        created_on__lt=cutoff_time
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} expired verification codes")
    return deleted_count
