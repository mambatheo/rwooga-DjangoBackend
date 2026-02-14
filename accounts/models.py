import uuid
import random
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
    
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        null=False,
        blank=False,
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
    
    is_active = models.BooleanField(_('active'), default=False)
    is_staff = models.BooleanField(_('staff status'), default=False)  
    
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)  
    
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
    RESET_PASSWORD = 'RESET_PASSWORD'

    LABEL_CHOICES = [
        (REGISTER, 'Register'),
        (RESET_PASSWORD, 'Reset Password'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_codes'
    )

    
    code = models.CharField(max_length=6, null=True, blank=True, db_index=True)  
    label = models.CharField(max_length=30, choices=LABEL_CHOICES)
    email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Verification Code'
        verbose_name_plural = 'Verification Codes'
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['email', 'is_verified']),
            models.Index(fields=['created_on']),
        ]

    def __str__(self):
        return f"{self.email} - {self.label} - {'Used' if self.is_verified else 'Active'}"

    @staticmethod
    def generate_code():
        """Generate a random 6-digit verification code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    @property
    def is_expired(self):
        expiry_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY_MINUTES', 10)
        return timezone.now() > self.created_on + timedelta(minutes=expiry_minutes)

    @property
    def is_valid(self):
        return not self.is_verified and not self.is_expired