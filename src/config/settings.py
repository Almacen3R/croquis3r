import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or ("local-prototype-do-not-deploy" if DEBUG else "")
if not DEBUG and (len(SECRET_KEY) < 32 or SECRET_KEY.startswith("local-")):
    raise ImproperlyConfigured("Configure una DJANGO_SECRET_KEY segura para producción.")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
CSRF_TRUSTED_ORIGINS = [v for v in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if v]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "catalog", "sketches",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "src/templates"],
              "APP_DIRS": True, "OPTIONS": {"context_processors": [
                  "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
                  "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")
if DB_ENGINE == "postgres":
    DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.getenv("POSTGRES_DB", "croquis3r"),
        "USER": os.getenv("POSTGRES_USER", "croquis3r_app"), "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.getenv("POSTGRES_HOST", "db"), "PORT": os.getenv("POSTGRES_PORT", "5432")}}
elif DB_ENGINE == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    raise ImproperlyConfigured("DB_ENGINE debe ser sqlite o postgres.")
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es-cr"
TIME_ZONE = "America/Costa_Rica"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "src/static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/admin/login/"
DATA_UPLOAD_MAX_MEMORY_SIZE = 1_048_576
if not DEBUG:
    # Un piloto HTTP en LAN puede desactivarlo explícitamente, manteniendo DEBUG=0.
    # Para publicar por HTTPS debe conservarse el valor predeterminado seguro.
    SESSION_COOKIE_SECURE = os.getenv("DJANGO_COOKIE_SECURE", "1") == "1"
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
