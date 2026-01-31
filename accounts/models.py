import uuid
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):   

    def create_user(self, email, full_name, phone_number, password=None, **extra_fields):       
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not phone_number:
            raise ValueError(_('The Phone Number field must be set'))
        if not full_name:
            raise ValueError(_('Your Full names are needed'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            phone_number=phone_number,  
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, phone_number, password=None, **extra_fields):
       
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')  
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email, full_name, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):     
    
    STAFF = 'STAFF'
    ADMIN = 'ADMIN'
    CUSTOMER = 'CUSTOMER'
    
    USER_TYPE_CHOICES = [
        (STAFF, 'Staff Member'),
        (ADMIN, 'Administrator'),
        (CUSTOMER, 'Customer'),
    ]
    
    # UUID Primary Key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    phone_number = models.CharField(
        max_length=10,  
        unique=True,
    )
    
    full_name = models.CharField(_('full name'), max_length=50)
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=CUSTOMER 
    )    
    
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)  
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  
    
    objects = UserManager()    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']  
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name  
    
    @property
    def is_admin(self):        
        return self.user_type == self.ADMIN  
    
    @property
    def is_staff_member(self): 
        return self.user_type == self.STAFF
    
    @property
    def is_customer(self):
        return self.user_type == self.CUSTOMER  
    
    @property
    def display_name(self):
        return self.full_name if self.full_name else self.email


class VerificationCode(models.Model):   
    
    REGISTER = 'REGISTER'
    EMAIL_VERIFICATION = 'EMAIL_VERIFICATION'
    RESET_PASSWORD = 'RESET_PASSWORD'
    CHANGE_EMAIL = 'CHANGE_EMAIL'

    LABEL_CHOICES = [
        (REGISTER, 'Register'),
        (EMAIL_VERIFICATION, 'Email Verification'),
        (RESET_PASSWORD, 'Reset Password'),
        (CHANGE_EMAIL, 'Change Email'),
    ]

    # UUID Primary Key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  
        blank=True,
        null=True,
        related_name='verification_codes'
    )
    code = models.CharField(max_length=6)
    label = models.CharField(
        max_length=30,
        choices=LABEL_CHOICES,
        default=REGISTER
    )
    email = models.EmailField(max_length=255)  
    email_verified = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'code', 'label']),
            models.Index(fields=['created_on']),
        ]
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.email} - {self.label} - {self.code}"

    @property
    def is_valid(self):
        """Check if verification code is still valid (not expired and not used)"""
        expiration_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 10)
        expiration_time = self.created_on + timedelta(minutes=expiration_minutes)        
        return timezone.now() < expiration_time and not self.email_verified
    
    @property
    def is_pending(self):
        """Check if verification code is pending (valid and not verified)"""
        return not self.email_verified and self.is_valid
    
    @property
    def is_expired(self):
        """Check if verification code has expired"""
        expiration_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 10)
        expiration_time = self.created_on + timedelta(minutes=expiration_minutes)
        return timezone.now() >= expiration_time