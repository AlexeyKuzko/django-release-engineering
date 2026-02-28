from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "django_educational_demo_application.users"
    verbose_name = _("Users")

    def ready(self):
        """Import signals when Django starts."""
        from . import signals  # noqa: F401
