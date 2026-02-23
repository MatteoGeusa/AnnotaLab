"""
Django settings for backend project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#  ENVIRONMENT VARIABLES CONFIGURATION

SECRET_KEY = os.environ.get('SECRET_KEY')


DEBUG = int(os.environ.get('DEBUG', 0))


ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'annotation': { 
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

UNFOLD = {
    # Titolo nella barra laterale
    "SITE_TITLE": "Annotation Portal",
    
    # Sottotitolo o header
    "SITE_HEADER": "Pannel Admin",
    
    # Link quando clicchi sul logo/titolo (di solito la homepage del sito o la dashboard)
    "SITE_URL": "/",

    # Colori della sidebar (opzionale)
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
        },
    },

    # Sidebar configuration
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Annotation",
                "items": [
                    {
                        "title": "Projects",
                        "link": "/admin/annotation/project/",
                        "icon": "folder",
                    },
                    {
                        "title": "Annotators",
                        "link": "/admin/annotation/annotator/",
                        "icon": "group",
                    },
                ],
            },
            {
                "title": "Auth",
                "items": [
                    {
                        "title": "Users",
                        "link": "/admin/auth/user/",
                        "icon": "person",
                    },
                ],
            },
        ],
    },
}

INSTALLED_APPS = [
    'unfold',
    "unfold.contrib.filters",       
    "unfold.contrib.forms",         
    "unfold.contrib.import_export", 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'import_export',
    'annotation',
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

#  CORS & CSRF CONFIGURATION

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 
    'http://localhost:80,http://127.0.0.1:80,http://localhost:5173,http://localhost:8080'
).split(',')

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 
    'http://localhost:8080,http://127.0.0.1:8080'
).split(',')

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'


# =========================================================
#  DATABASE
# =========================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'), 
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}


# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')