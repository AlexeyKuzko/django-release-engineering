"""Educational project management domain models."""

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """Educational course model."""

    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    def get_absolute_url(self) -> str:
        return reverse("projects:course_detail", kwargs={"pk": self.pk})

    @property
    def duration_days(self) -> int:
        """Calculate course duration in days."""
        return (self.end_date - self.start_date).days

    @property
    def status(self) -> str:
        """Return course status: upcoming, active, or completed."""
        today = timezone.now().date()
        if today < self.start_date:
            return "upcoming"
        if today > self.end_date:
            return "completed"
        return "active"

    def get_student_count(self) -> int:
        """Return number of enrolled students."""
        return self.enrollments.count()

    def get_project_count(self) -> int:
        """Return number of projects in this course."""
        return self.projects.count()


class Student(models.Model):
    """Student profile model."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_id = models.CharField(max_length=50, unique=True, db_index=True)
    group = models.CharField(max_length=50, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username"]
        verbose_name = _("Student")
        verbose_name_plural = _("Students")

    def __str__(self) -> str:
        return f"{self.user.username} ({self.student_id})"

    def get_absolute_url(self) -> str:
        return reverse("projects:student_detail", kwargs={"pk": self.pk})

    def get_active_projects(self) -> models.QuerySet:
        """Return student's active projects."""
        return self.projects.filter(status="in_progress")

    def get_completed_projects(self) -> models.QuerySet:
        """Return student's completed projects."""
        return self.projects.filter(status="completed")

    def get_average_score(self) -> float | None:
        """Calculate average score across all graded projects."""
        graded = self.projects.exclude(score__isnull=True)
        if graded.exists():
            return graded.aggregate(models.Avg("score"))["score__avg"]
        return None


class Enrollment(models.Model):
    """Student enrollment in a course."""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["student", "course"]
        ordering = ["-enrolled_at"]
        verbose_name = _("Enrollment")
        verbose_name_plural = _("Enrollments")

    def __str__(self) -> str:
        return f"{self.student} in {self.course}"


class Project(models.Model):
    """Educational project model with status workflow."""

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("in_progress", _("In Progress")),
        ("review", _("Under Review")),
        ("completed", _("Completed")),
        ("archived", _("Archived")),
    ]

    PRIORITY_CHOICES = [
        ("low", _("Low")),
        ("medium", _("Medium")),
        ("high", _("High")),
    ]

    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="medium",
    )
    score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    repository_url = models.URLField(blank=True, max_length=500)
    deployed_url = models.URLField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.student.user.username})"

    def save(self, *args, **kwargs) -> None:
        """Auto-update completed_at when status changes to completed."""
        if self.status == "completed" and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != "completed":
            self.completed_at = None
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("projects:project_detail", kwargs={"pk": self.pk})

    def can_transition_to(self, new_status: str) -> bool:
        """Check if status transition is valid."""
        allowed_transitions = {
            "draft": ["in_progress", "archived"],
            "in_progress": ["review", "draft", "archived"],
            "review": ["completed", "in_progress", "draft"],
            "completed": ["in_progress", "archived"],
            "archived": ["draft"],
        }
        return new_status in allowed_transitions.get(self.status, [])

    def transition_to(self, new_status: str, user=None) -> bool:
        """
        Transition project to new status with validation.

        Returns True if transition was successful, False otherwise.
        """
        if not self.can_transition_to(new_status):
            return False

        self.status = new_status
        if new_status == "completed" and self.score is None:
            self.score = 0
        self.save()

        ProjectStatusLog.objects.create(
            project=self,
            old_status=self.status,
            new_status=new_status,
            changed_by=user.user if hasattr(user, "user") else user,
        )
        return True

    @property
    def is_overdue(self) -> bool:
        """Check if project is past deadline."""
        if self.deadline and self.status not in ["completed", "archived"]:
            return timezone.now().date() > self.deadline
        return False

    @property
    def days_until_deadline(self) -> int | None:
        """Return days until deadline, or None if no deadline."""
        if self.deadline:
            return (self.deadline - timezone.now().date()).days
        return None

    def get_task_count(self) -> int:
        """Return number of tasks in this project."""
        return self.tasks.count()

    def get_completed_task_count(self) -> int:
        """Return number of completed tasks."""
        return self.tasks.filter(is_completed=True).count()

    @property
    def progress_percentage(self) -> int:
        """Calculate project progress based on completed tasks."""
        total = self.get_task_count()
        if total == 0:
            return 0
        return int((self.get_completed_task_count() / total) * 100)


class Task(models.Model):
    """Task within a project."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")

    def __str__(self) -> str:
        return f"{self.title} ({self.project.title})"

    def save(self, *args, **kwargs) -> None:
        """Auto-update completed_at when task is completed."""
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)


class ProjectStatusLog(models.Model):
    """Log of project status changes for audit trail."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = _("Status Log")
        verbose_name_plural = _("Status Logs")

    def __str__(self) -> str:
        return f"{self.project.title}: {self.old_status} → {self.new_status}"
