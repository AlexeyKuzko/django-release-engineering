# Generated migration to add Student profiles for existing users.

from django.conf import settings
from django.db import migrations


def create_student_profiles_for_existing_users(apps, schema_editor) -> None:
    """
    Create Student profiles for all existing users without one.

    This ensures backward compatibility after enabling automatic
    Student profile creation for new users.
    """
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Student = apps.get_model("projects", "Student")

    users_without_profile = User.objects.filter(
        student_profile__isnull=True,
    )

    for user in users_without_profile:
        Student.objects.create(
            user=user,
            student_id=f"STU{user.pk:05d}",
        )


def reverse_migration(apps, schema_editor) -> None:
    """Remove all Student profiles (reverse migration)."""
    Student = apps.get_model("projects", "Student")
    Student.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            create_student_profiles_for_existing_users,
            reverse_migration,
        ),
    ]
