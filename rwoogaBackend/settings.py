import os
from decouple import config
from dotenv import load_dotenv
from datetime import timedelta
from pathlib import Path
import dj_database_url 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)


# DEBUG = True 

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

# Application definition
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  
    'corsheaders',
    'django_extensions',
    'django_filters',
    'drf_spectacular',   
    'accounts',
    'orders',
    'pricing',
    'products',
    'utils',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
 
ROOT_URLCONF = 'rwoogaBackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rwoogaBackend.wsgi.application'

# Database Configuration - Optimized for Koyeb + Supabase
if config('DATABASE_URL', default=None):
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,  
            conn_health_checks=True,  
            ssl_require=True,  
        )
    }
else:
    # Fallback for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('NAME'),
            'USER': config('USER'),
            'PASSWORD': config('PASSWORD'),
            'HOST': config('HOST', default='localhost'),
            'PORT': config('PORT', cast=int, default=5432),
            'OPTIONS': {
                'sslmode': 'require',  
            },
            'CONN_MAX_AGE': 600,  
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email context variables
COMPANY_LOGO_URL = config('COMPANY_LOGO_URL', default='')
YOUTUBE = config('YOUTUBE', default='https://youtube.com/')
INSTAGRAM = config('INSTAGRAM', default='https://www.instagram.com/rwooga.ent')
TWITTER = config('TWITTER', default='https://x.com/PhedoKat')
TIKTOK = config('TIKTOK', default='https://www.tiktok.com/@phedish')

# Icon URLs
YOUTUBE_ICON_URL = config('YOUTUBE_ICON_URL', default='')
INSTAGRAM_ICON_URL = config('INSTAGRAM_ICON_URL', default='')
TWITTER_ICON_URL = config('TWITTER_ICON_URL', default='')
TIKTOK_ICON_URL = config('TIKTOK_ICON_URL', default='')

STORAGES = {   
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://rwooga-project.vercel.app",
    "https://www.rwooga.com",
    "https://rwooga-project.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True



SITE_URL =  "https://rwooga-project.vercel.app"   
COMPANY_NAME = "Rwooga"                 
SUPPORT_EMAIL = "support@rwooga.com"
VERIFICATION_CODE_EXPIRY_MINUTES = 10 



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# Site Configuration
SITE_URL = config('SITE_URL', default='http://localhost:3000')
COMPANY_NAME = config('COMPANY_NAME', default='Rwooga')
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@rwooga.com')
VERIFICATION_CODE_EXPIRY_MINUTES = config('VERIFICATION_CODE_EXPIRY_MINUTES', default=10, cast=int)

# Security Settings
MAX_LOGIN_ATTEMPTS = config('MAX_LOGIN_ATTEMPTS', default=5, cast=int)
ACCOUNT_LOCKOUT_MINUTES = config('ACCOUNT_LOCKOUT_MINUTES', default=30, cast=int)
VERIFICATION_RESEND_COOLDOWN_MINUTES = config('VERIFICATION_RESEND_COOLDOWN_MINUTES', default=2, cast=int)

# Session Settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production Security (only when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

# API Documentation Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'Rwooga Backend API',
    'DESCRIPTION': 'API for user authentication and 3D services',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
