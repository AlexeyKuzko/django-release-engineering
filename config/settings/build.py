import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "build")

DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}
