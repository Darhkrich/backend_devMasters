from datetime import timedelta
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

from config.env import env, env_bool, env_int, env_list

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_ENV = env("APP_ENV", default="development").strip().lower()
DEBUG = env_bool("DEBUG", default=APP_ENV in {"development", "dev"})

SECRET_KEY = env("SECRET_KEY", default="")
ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1" if DEBUG else "",
)
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
AUTH_COOKIE_DOMAIN = env("AUTH_COOKIE_DOMAIN", default="").strip() or None
AUTH_COOKIE_PATH = env("AUTH_COOKIE_PATH", default="/").strip() or "/"
AUTH_COOKIE_SAMESITE = env(
    "AUTH_COOKIE_SAMESITE",
    default="Lax" if DEBUG else "None",
).strip().title()
AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", default=not DEBUG)

if AUTH_COOKIE_SAMESITE == "None":
    AUTH_COOKIE_SECURE = True

AUDIT_LOG_SIGNING_KEY = env("AUDIT_LOG_SIGNING_KEY", default=SECRET_KEY)
AUDIT_LOG_RETENTION_DAYS = env_int("AUDIT_LOG_RETENTION_DAYS", 365)
SECURITY_EVENT_RETENTION_DAYS = env_int("SECURITY_EVENT_RETENTION_DAYS", 180)
LOGIN_HISTORY_RETENTION_DAYS = env_int("LOGIN_HISTORY_RETENTION_DAYS", 180)
DEVICE_SESSION_RETENTION_DAYS = env_int("DEVICE_SESSION_RETENTION_DAYS", 90)
DEVICE_TRUST_DAYS = env_int("DEVICE_TRUST_DAYS", 30)
SENSITIVE_ADMIN_PATH_PREFIXES = env_list(
    "SENSITIVE_ADMIN_PATH_PREFIXES",
    default="/admin,/api/v1/security,/api/v1/audit",
)
API_DEFAULT_VERSION = env("API_DEFAULT_VERSION", default="v1")
API_SUPPORTED_VERSIONS = env_list("API_SUPPORTED_VERSIONS", default="v1")
API_DEPRECATED_VERSIONS = {}
API_DEPRECATION_POLICY_URL = env(
    "API_DEPRECATION_POLICY_URL",
    default="https://example.com/api-deprecation-policy",
)
API_CACHE_TTL_SECONDS = env_int("API_CACHE_TTL_SECONDS", 60)
TASK_QUEUE_MODE = env(
    "TASK_QUEUE_MODE",
    default="sync",
)
TASK_QUEUE_WORKERS = env_int("TASK_QUEUE_WORKERS", 4)
REQUEST_SLOW_THRESHOLD_MS = env_int("REQUEST_SLOW_THRESHOLD_MS", 500)
REDIS_URL = env("REDIS_URL", default="")
REDIS_CACHE_URL = env("REDIS_CACHE_URL", default=REDIS_URL)
METRICS_AUTH_TOKEN = env("METRICS_AUTH_TOKEN", default="")
WORKER_POLL_INTERVAL_SECONDS = env_int("WORKER_POLL_INTERVAL_SECONDS", 5)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "channels",
    "apps.core",
    "apps.users",
    "apps.workforce",
    "apps.audit",
    "apps.security",
    "apps.clients",
    "apps.services",
    "apps.pricing",
    "apps.templates",
    "apps.inquiries",
    "apps.orders",
    "apps.messages_app",
    "apps.files",
    "apps.support",
    "apps.automation",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.core.middleware.RequestTracingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.security.middleware.BlockIPMiddleware",
    "apps.security.middleware.SecurityHeadersMiddleware",
    "apps.audit.middleware.AuditRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.APIVersioningMiddleware",
    "apps.core.middleware.GlobalExceptionMiddleware",
    "apps.core.middleware.CoepMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

]
ROOT_URLCONF = 'config.urls'

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    default=f"{FRONTEND_URL},http://localhost:3000,http://127.0.0.1:3000",
)
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["X-CSRFToken"]
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    default=",".join(CORS_ALLOWED_ORIGINS),
)

SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default="").strip() or None
SESSION_COOKIE_PATH = env("SESSION_COOKIE_PATH", default="/").strip() or "/"
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=AUTH_COOKIE_SECURE)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = env(
    "SESSION_COOKIE_SAMESITE",
    default=AUTH_COOKIE_SAMESITE,
).strip().title()
CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default=AUTH_COOKIE_DOMAIN or "").strip() or None
CSRF_COOKIE_PATH = env("CSRF_COOKIE_PATH", default="/").strip() or "/"
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=AUTH_COOKIE_SECURE)
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = env(
    "CSRF_COOKIE_SAMESITE",
    default=AUTH_COOKIE_SAMESITE,
).strip().title()
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.core.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "login": "5/min",
        "token_refresh": "20/hour",
        "register": "5/min",
        "password_reset": "3/min",
        "resend_verification": "5/min",
        "two_factor": "10/10min",
        "sensitive_user_action": "20/hour",
        "admin_action": "120/hour",
        "security_analytics": "60/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "apps.core.versioning.ProjectPathVersioning",
    "DEFAULT_VERSION": API_DEFAULT_VERSION,
    "ALLOWED_VERSIONS": API_SUPPORTED_VERSIONS,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOGIN_LOCKOUT_TIME": timedelta(minutes=15),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Backend API",
    "DESCRIPTION": "Monolith Backend System",
    "VERSION": "1.0.0",
}

AUTH_USER_MODEL = "users.User"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if APP_ENV in {"staging", "production", "prod"}:
    if REDIS_URL:
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {
                    "hosts": [REDIS_URL],
                },
            }
        }
    else:
        CHANNEL_LAYERS = {}
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "backend-enterprise-cache",
        "TIMEOUT": API_CACHE_TTL_SECONDS,
    }
}

DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'), conn_max_age=600, ssl_require=False)
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
PROJECT_FILE_UPLOAD_MAX_BYTES = env_int("PROJECT_FILE_UPLOAD_MAX_BYTES", 15 * 1024 * 1024)
PROJECT_FILE_ALLOWED_EXTENSIONS = env_list(
    "PROJECT_FILE_ALLOWED_EXTENSIONS",
    default=".pdf,.doc,.docx,.txt,.rtf,.csv,.xls,.xlsx,.png,.jpg,.jpeg,.webp,.zip",
)
PROJECT_FILE_ALLOWED_CONTENT_TYPES = env_list(
    "PROJECT_FILE_ALLOWED_CONTENT_TYPES",
    default=(
        "application/pdf,text/plain,text/csv,application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "image/png,image/jpeg,image/webp,application/zip,application/x-zip-compressed,"
        "application/octet-stream"
    ),
)
PROJECT_FILE_ALLOWED_URL_SCHEMES = env_list(
    "PROJECT_FILE_ALLOWED_URL_SCHEMES",
    default="https",
)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX", default="[Enterprise Admin] ")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or env(
    "DEFAULT_FROM_EMAIL",
    default="no-reply@example.com",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "apps.core.observability.RequestContextFilter",
        }
    },
    "formatters": {
        "structured": {
            "()": "apps.core.observability.StructuredFormatter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "structured",
        }
    },
    "loggers": {
        "backend.request": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "backend.task_worker": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
