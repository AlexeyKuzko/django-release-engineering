from . import base as base_settings

SECRET_KEY = "django-insecure-build-key"

DEBUG = False

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = base_settings.INSTALLED_APPS
MIDDLEWARE = base_settings.MIDDLEWARE
TEMPLATES = base_settings.TEMPLATES
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}
STATIC_URL = base_settings.STATIC_URL
STATIC_ROOT = base_settings.STATIC_ROOT
