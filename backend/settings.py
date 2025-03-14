from datetime import timedelta
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-zqnyw=-wzr86$00ie+4cws7ag1vxdf@z(@4q(&)=4o5u3jwash'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost','192.168.2.233','192.168.48.121', '127.0.0.1',]
# ALLOWED_HOSTS = ["*"]

AUTH_USER_MODEL='users.CustomUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'users',
    'admins',
]
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',
    ]
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Access token expires in 15 min
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7), 
    'BLACKLIST_AFTER_ROTATION': True,  # Enable token blacklisting
    'ROTATE_REFRESH_TOKENS': True,     # Rotate refresh tokens after use
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'social_media_db',
        'USER': 'django_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost' ,
        'PORT': '5432',
    }
}



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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

CORS_ALLOW_CREDENTIALS = True  # For cross-domain cookies
CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = [
    "https://192.168.2.233",  # frontend domain here
    "http://192.168.2.233",  
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
]



EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'ecesoclabs@iiitd.ac.in'
EMAIL_HOST_PASSWORD = 'eksvvyqulsanjjlz'

CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_HTTPONLY = False  
CSRF_COOKIE_SAMESITE = "Lax"  
CORS_ALLOW_CREDENTIALS = True
CSRF_USE_SESSIONS = False  

ROOT_URLCONF = 'backend.urls'
STATIC_URL = 'static/'
MEDIA_URL = '/media/'

#Development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
STATIC_ROOT=BASE_DIR/ 'static'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
CSRF_COOKIE_SECURE = False
CORS_ALLOW_ALL_ORIGINS = True
#production
# MEDIA_ROOT = "/var/www/RansomHub-Backend/media/"  
# STATIC_ROOT = "/var/www/RansomHub-Backend/static/"  
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# CSRF_COOKIE_SECURE = True  
# CORS_ALLOWED_ORIGINS = [
#     "http://192.168.2.233",
#     "https://192.168.2.233",
#     "http://localhost:3000",  
# ]