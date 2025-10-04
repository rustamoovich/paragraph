"""
Базовые настройки Django для обоих окружений.
"""

from pathlib import Path
import os

from dotenv import load_dotenv


# Корень проекта (папка с manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Загружаем переменные окружения из .env (если он есть)
load_dotenv(BASE_DIR / ".env")


# Безопасность
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key-change-me",
)

DEBUG = False  # Переопределяется в dev.py

ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h] or []


# Приложения
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Проектные приложения
    "apps.users",
    "apps.orders",
    "apps.payments",
    "apps.telegram_bot",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"


# Шаблоны
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# База данных (конкретизируется в dev/prod)
DATABASES = {
    "default": {
        "ENGINE": "djongo",
        "NAME": os.getenv("MONGO_DB_NAME", "paragraph"),
        "ENFORCE_SCHEMA": False,
        "CLIENT": {
            # Предпочтительно использовать полный URI
            "host": os.getenv("MONGO_URI", "mongodb://localhost:27017/paragraph"),
        },
    }
}


# Валидаторы паролей
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


# Локализация
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Tashkent")
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Форматы даты и времени для локализации
DATE_FORMAT = "d.m.Y"
DATETIME_FORMAT = "d.m.Y H:i:s"
TIME_FORMAT = "H:i:s"


# Статика и медиа
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# Логирование (минимум, можно расширить в prod)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}


# Настройки Telegram/OTP
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL", "/")
LOGOUT_REDIRECT_URL = os.getenv("LOGOUT_REDIRECT_URL", "/")

