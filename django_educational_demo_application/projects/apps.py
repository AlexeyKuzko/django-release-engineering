"""App configuration for projects app."""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Projects app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_educational_demo_application.projects"
    verbose_name = "Educational Projects"
