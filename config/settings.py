from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-)76zvrn)+9frg^h5=7wq!l=xlrqi-57@#7yjq3f(s14$$khudk"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['kitup.duckdns.org', '3.37.88.175', 'localhost', '127.0.0.1',]

CSRF_TRUSTED_ORIGINS = [
    'http://kitup.duckdns.org',
    'http://kitup.duckdns.org:8000',
    'https://kitup.duckdns.org',
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third-party apps
    "rest_framework",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.kakao",
    "allauth.socialaccount.providers.naver",
    "allauth.socialaccount.providers.github",
    
    # Local apps
    "apps.accounts.apps.AccountsConfig",
    "apps.projects.apps.ProjectsConfig",
    "apps.teams.apps.TeamsConfig",
    "apps.guides.apps.GuidesConfig",
    "apps.reflections.apps.ReflectionsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    
    "allauth.account.middleware.AccountMiddleware",
    "apps.accounts.middleware.RequireProfileMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# AllAuth settings 
SITE_ID = 1
AUTH_USER_MODEL = "accounts.User"

# allauth 설정
ACCOUNT_LOGIN_METHODS = {"username", "email"}  # 아이디 또는 이메일로 로그인
ACCOUNT_EMAIL_REQUIRED = True  # 이메일 필수
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # 이메일 인증 필수
ACCOUNT_SIGNUP_FIELDS = [
    "username*",
    "email*",
    "password1*",
    "password2*",
]
ACCOUNT_CONFIRM_EMAIL_ON_GET = True  # 이메일 링크 클릭만으로 인증 완료
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # 인증 링크 유효기간 (일)
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[KITUP] "  # 이메일 제목 접두사

# 이메일 발송 설정
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", '"KITUP" <noreply@kitup.com>')

# 비밀번호 재설정
ACCOUNT_PASSWORD_RESET_ON_CHANGE = False  # 비밀번호 변경 시 재로그인 불필요

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"          # 로그인 성공 후
LOGOUT_REDIRECT_URL = "/"         # 로그아웃 후

ACCOUNT_SIGNUP_REDIRECT_URL = "/" # 회원가입 완료 후(가능한 버전에서 동작)
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": GOOGLE_CLIENT_ID,
                "secret": GOOGLE_CLIENT_SECRET,
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    },
    "kakao": {
        "APPS": [
            {
                "client_id": os.getenv("KAKAO_CLIENT_ID"),
                "secret": os.getenv("KAKAO_CLIENT_SECRET"),
                "key": "",
            }
        ]
    },
    "naver": {
        "APPS": [
            {
                "client_id": os.getenv("NAVER_CLIENT_ID"),
                "secret": os.getenv("NAVER_CLIENT_SECRET"),
                "key": "",
            }
        ],
    },
    "github": {
        "APPS": [
            {
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "key": "",
            }
        ],
        "SCOPE": ["user:email"],
    },
}


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ko"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework 설정
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    # 개발 중에는 인증 없이 API 테스트 가능하도록 설정
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# drf-spectacular 설정 (Swagger/OpenAPI)
SPECTACULAR_SETTINGS = {
    "TITLE": "StartLine Dev API",
    "DESCRIPTION": "StartLine Dev 프로젝트 API 문서",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "http://127.0.0.1:8000", "description": "local"},
    ],
}
