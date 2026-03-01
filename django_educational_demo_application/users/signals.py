"""Signals for automatic Student profile creation."""

from django.db.models import signals
from django.dispatch import receiver

from .models import User


@receiver(signals.post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs) -> None:
    """
    Create a Student profile for every newly created user.

    This ensures that all registered users automatically get the student role.
    """
    if created and not hasattr(instance, "student_profile"):
        from django_educational_demo_application.projects.models import Student

        Student.objects.create(
            user=instance,
            student_id=f"STU{instance.pk:05d}",
        )
