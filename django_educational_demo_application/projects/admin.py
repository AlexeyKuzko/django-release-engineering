"""Admin configuration for educational project management."""

from django.contrib import admin

from .models import Course
from .models import Enrollment
from .models import Project
from .models import ProjectStatusLog
from .models import Student
from .models import Task


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin for Course model."""

    list_display = ["code", "name", "start_date", "end_date", "is_active"]
    list_filter = ["is_active", "start_date"]
    search_fields = ["code", "name", "description"]
    ordering = ["-start_date"]
    readonly_fields = ["duration_days", "status"]

    def duration_days(self, obj):
        return obj.duration_days

    def status(self, obj):
        return obj.status


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin for Student model."""

    list_display = ["user", "student_id", "group", "enrolled_at"]
    list_filter = ["group", "enrolled_at"]
    search_fields = ["user__username", "student_id", "group"]
    ordering = ["user__username"]
    readonly_fields = ["enrolled_at", "student_id"]
    raw_id_fields = ["user"]

    def has_add_permission(self, request, obj=None) -> bool:
        """
        Prevent manual addition - student profile is created automatically.

        Admins can still edit group field for existing students.
        """
        return False


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin for Enrollment model."""

    list_display = ["student", "course", "enrolled_at", "is_active"]
    list_filter = ["is_active", "course"]
    search_fields = ["student__user__username", "course__code"]
    ordering = ["-enrolled_at"]
    raw_id_fields = ["student", "course"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for Project model."""

    list_display = [
        "title",
        "student",
        "course",
        "status",
        "priority",
        "score",
        "deadline",
        "created_at",
        "is_overdue_display",
    ]
    list_filter = ["status", "priority", "course", "deadline"]
    search_fields = ["title", "description", "student__user__username", "course__code"]
    ordering = ["-created_at"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "completed_at",
        "progress_percentage",
    ]
    raw_id_fields = ["student", "course"]
    date_hierarchy = "created_at"

    @admin.display(
        description="Overdue",
        boolean=True,
    )
    def is_overdue_display(self, obj):
        return obj.is_overdue

    @admin.display(
        description="Progress",
    )
    def progress_percentage(self, obj):
        return obj.progress_percentage


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin for Task model."""

    list_display = ["title", "project", "is_completed", "order", "created_at"]
    list_filter = ["is_completed", "project__course"]
    search_fields = ["title", "description", "project__title"]
    ordering = ["project", "order", "created_at"]
    readonly_fields = ["created_at", "completed_at"]
    raw_id_fields = ["project"]


@admin.register(ProjectStatusLog)
class ProjectStatusLogAdmin(admin.ModelAdmin):
    """Admin for ProjectStatusLog model."""

    list_display = ["project", "old_status", "new_status", "changed_at", "changed_by"]
    list_filter = ["old_status", "new_status", "changed_at"]
    search_fields = ["project__title", "changed_by__username"]
    ordering = ["-changed_at"]
    readonly_fields = ["changed_at"]
    raw_id_fields = ["project", "changed_by"]
