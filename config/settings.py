
from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('Set SECRET_KEY in the environment.')

DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'noteapp.apps.NoteappConfig',
    'rest_framework',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get('DB_NAME', 'noteapp_db'),
        "USER": os.environ.get('DB_USER', ''),
        "PASSWORD": os.environ.get('DB_PASSWORD', ''),
        "HOST": os.environ.get('DB_HOST', 'localhost'),
        "PORT": os.environ.get('DB_PORT', '3306'),
    }
}
if not DATABASES['default']['USER'] or not DATABASES['default']['PASSWORD']:
    raise ImproperlyConfigured('Set DB_USER and DB_PASSWORD in the environment.')


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# Production security settings; enable HSTS only after HTTPS is confirmed.
SECURE_SSL_REDIRECT = os.environ.get(
    'SECURE_SSL_REDIRECT',
    str(not DEBUG),
).lower() == 'true'
SESSION_COOKIE_SECURE = os.environ.get(
    'SESSION_COOKIE_SECURE',
    str(not DEBUG),
).lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get(
    'CSRF_COOKIE_SECURE',
    str(not DEBUG),
).lower() == 'true'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'false',
).lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get(
    'SECURE_HSTS_PRELOAD',
    'false',
).lower() == 'true'
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
_email_smtp_requested = bool(
    os.environ.get('EMAIL_HOST')
    or (os.environ.get('EMAIL_HOST_USER') and os.environ.get('EMAIL_HOST_PASSWORD'))
)
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
    if _email_smtp_requested
    else 'django.core.mail.backends.console.EmailBackend',
)
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587' if EMAIL_HOST == 'smtp.gmail.com' else '25'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get(
    'EMAIL_USE_TLS',
    'true' if EMAIL_HOST == 'smtp.gmail.com' else 'false',
).lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', '').lower() == 'true'
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '10'))
DEFAULT_FROM_EMAIL = (
    EMAIL_HOST_USER
    if EMAIL_HOST == 'smtp.gmail.com' and EMAIL_HOST_USER
    else os.environ.get(
        'DEFAULT_FROM_EMAIL',
        EMAIL_HOST_USER or 'Notebook <noreply@localhost>',
    )
)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'note_list'
LOGOUT_REDIRECT_URL = 'note_list'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Notebook API',
    'DESCRIPTION': 'REST API for managing personal notes.',
    'VERSION': '1.0.0',
}