# coding: utf-8
"""
Django settings for auth_apps project.

Generated by 'django-admin startproject' using Django 1.8.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a&5^-%7tpg1d%8ti9&qw7i)m19xv%mo*q^ej6+4max2+5sz-jx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.getenv('DJANGO_DEBUG', 0))
TEST = int(os.getenv('DJANGO_TEST', 0))

ALLOWED_HOSTS = [os.getenv('DJANGO_HOST')]


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third part apps
    'oauth2_provider',
    'rest_framework',
    'corsheaders',
    'widget_tweaks',
    'datetimewidget',
    'db_file_storage',
    'djcelery',
    # my apps
    'common',
    'edu_info',
    'auth_user',
    'custom_oauth2',
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'auth_apps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'custom_oauth2', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'auth_apps.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_ENV_MYSQL_DATABASE'),
        'USER': os.getenv('DB_ENV_MYSQL_USER'),
        'PASSWORD': os.getenv('DB_ENV_MYSQL_PASSWORD'),
        'HOST': os.getenv('DB_PORT_3306_TCP_ADDR'),
        'PORT': os.getenv('DB_PORT_3306_TCP_PORT'),
        'OPTIONS': {
            'charset': 'utf8',
            'init_command': 'SET storage_engine=InnoDB,character_set_connection=utf8,collation_connection=utf8_unicode_ci',
        },
        'TEST': {
            'NAME': 'test_account_center',
        },
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = [
    ('zh-hans', u'简体中文'),
    ('en-us', 'English'),
]
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

DEFAULT_FILE_STORAGE = 'db_file_storage.storage.DatabaseFileStorage'

# email settings
EMAIL_USE_SSL = int(os.getenv('EMAIL_USE_SSL', 0))
EMAIL_USE_TLS = int(os.getenv('EMAIL_USE_TLS', 0))
EMAIL_HOST = os.getenv('EMAIL_HOST', None)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 0))
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# auth setting
AUTH_USER_MODEL = 'auth_user.TechUUser'
AUTHENTICATION_BACKENDS = [
    # 'oauth_provider.backends.OAuth2Backend',  # for OAuth2 login users
    'auth_user.backend.TechUBackend',  # for account center site
    'auth_user.backend.XPlatformBackend',  # for users from xplatform
    'django.contrib.auth.backends.ModelBackend',  # for admin site
]

# password settings
PASSWORD_HASHERS = [
    'auth_user.hashers.TechUPasswordHasher',
]

# CORS settings
CORS_ORIGIN_ALLOW_ALL = True

# django oauth toolkit settings
OAUTH2_PROVIDER_APPLICATION_MODEL = 'custom_oauth2.TechUApplication'
OAUTH2_PROVIDER = {
    'SCOPES': {
        'user': 'Read user info scope',
        'group': 'Read group info scope',
    },
    'DEFAULT_SCOPES': ['user', 'group'],
    'OAUTH2_VALIDATOR_CLASS': 'custom_oauth2.oauth2_validators.TechUOAuth2Validator',
    'APPLICATION_MODEL': 'custom_oauth2.TechUApplication',
}

# rest framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

# loggings
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'oauthlib': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'auth_user': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'common': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# security setting
SECURE_SSL_REDIRECT = True
if TEST:
    SECURE_SSL_REDIRECT = False 
ENABLE_MOBILE_PASSWORD_VERIFY = True
TECHU_FRONTEND_SALT = 'cloud_homework-'
TECHU_BACKEND_SALT = 'yzy-'
DEFAULT_REQUEST_TIMEOUT = 3
MOBILE_CODE_COUNTDOWN = 60  # seconds

# cache setting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': os.getenv('MEMCACHED_ADDR') + ':' + os.getenv('MEMCACHED_PORT'),
    }
}

# SMS service setting
SENDSMS_BACKEND = 'common.sms_backends.TechUSMSBackend'
if TEST:
    SENDSMS_BACKEND='sendsms.backends.locmem.SmsBackend'
SMS_SERVICE_URL = os.getenv('SMS_SERVICE_URL')
SMS_REQUEST_TIMEOUT = 3  # seconds

# XPLATFORM SERVICE setting
XPLATFORM_SERVICE = {
    'URL': os.getenv('XPLATFORM_SERVICE_URL') # 'https://dev.login.yunxiaoyuan.com' if DEBUG else 'https://login.yunxiaoyuan.com',
    'APP_ID': '98008',
    'SERVER_KEY': 'C6F653399B9A15E053469A66',
    'CLIENT_KEY': '9852C11D7FF63FDE5732A4BA',
    'TIMEOUT': 3,
}

# celery settings
BROKER_URL = os.getenv('CELERY_BROKER_URL') 
# CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = TIME_ZONE
if TEST:
    CELERY_ALWAYS_EAGER=True
