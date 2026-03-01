"""Tests for educational project management models."""

import pytest
from django.utils import timezone

from django_educational_demo_application.projects.models import Course
from django_educational_demo_application.projects.models import Enrollment
from django_educational_demo_application.projects.models import Project
from django_educational_demo_application.projects.models import ProjectStatusLog
from django_educational_demo_application.projects.models import Task
from django_educational_demo_application.users.tests.factories import UserFactory


@pytest.fixture
def course(db):
    """Create a test course."""
    return Course.objects.create(
        name="Test Course",
        code="TC101",
        description="A test course",
        start_date=timezone.now().date() - timezone.timedelta(days=30),
        end_date=timezone.now().date() + timezone.timedelta(days=60),
    )


@pytest.fixture
def student(db):
    """Create a test student."""
    user = UserFactory()
    # Student profile is automatically created by signal
    student_profile = user.student_profile
    student_profile.student_id = "STU001"
    student_profile.group = "Group A"
    student_profile.save()
    return student_profile


@pytest.fixture
def project(db, course, student):
    """Create a test project."""
    return Project.objects.create(
        title="Test Project",
        description="A test project",
        course=course,
        student=student,
        status="draft",
        priority="medium",
    )


class TestCourseModel:
    """Test Course model."""

    def test_str(self, course):
        assert str(course) == "TC101 - Test Course"

    def test_duration_days(self, course):
        assert course.duration_days == 90  # noqa: PLR2004

    def test_status_active(self, course):
        assert course.status == "active"

    def test_status_upcoming(self, db):
        course = Course.objects.create(
            name="Future Course",
            code="FC101",
            start_date=timezone.now().date() + timezone.timedelta(days=30),
            end_date=timezone.now().date() + timezone.timedelta(days=90),
        )
        assert course.status == "upcoming"

    def test_status_completed(self, db):
        course = Course.objects.create(
            name="Past Course",
            code="PC101",
            start_date=timezone.now().date() - timezone.timedelta(days=90),
            end_date=timezone.now().date() - timezone.timedelta(days=30),
        )
        assert course.status == "completed"

    def test_get_absolute_url(self, course):
        assert course.get_absolute_url() == f"/courses/{course.pk}/"


class TestStudentModel:
    """Test Student model."""

    def test_str(self, student):
        assert str(student) == f"{student.user.username} (STU001)"

    def test_get_absolute_url(self, student):
        assert student.get_absolute_url() == f"/students/{student.pk}/"

    def test_get_average_score(self, student, course):
        Project.objects.create(
            title="Project 1",
            description="Test",
            course=course,
            student=student,
            score=80,
            status="completed",
        )
        Project.objects.create(
            title="Project 2",
            description="Test",
            course=course,
            student=student,
            score=90,
            status="completed",
        )
        assert student.get_average_score() == 85.0  # noqa: PLR2004

    def test_get_average_score_no_projects(self, student):
        assert student.get_average_score() is None


class TestProjectModel:
    """Test Project model."""

    def test_str(self, project):
        assert str(project) == f"Test Project ({project.student.user.username})"

    def test_get_absolute_url(self, project):
        assert project.get_absolute_url() == f"/projects/{project.pk}/"

    def test_is_overdue(self, db, course, student):
        project = Project.objects.create(
            title="Overdue Project",
            description="Test",
            course=course,
            student=student,
            deadline=timezone.now().date() - timezone.timedelta(days=1),
            status="in_progress",
        )
        assert project.is_overdue is True

    def test_is_not_overdue_completed(self, db, course, student):
        project = Project.objects.create(
            title="Completed Project",
            description="Test",
            course=course,
            student=student,
            deadline=timezone.now().date() - timezone.timedelta(days=1),
            status="completed",
        )
        assert project.is_overdue is False

    def test_days_until_deadline(self, db, course, student):
        project = Project.objects.create(
            title="Future Project",
            description="Test",
            course=course,
            student=student,
            deadline=timezone.now().date() + timezone.timedelta(days=10),
        )
        assert project.days_until_deadline == 10  # noqa: PLR2004

    def test_can_transition_to_valid(self, project):
        assert project.can_transition_to("in_progress") is True
        assert project.can_transition_to("archived") is True
        assert project.can_transition_to("completed") is False

    def test_transition_to(self, project):
        user = UserFactory()
        result = project.transition_to("in_progress", user=user)
        assert result is True
        assert project.status == "in_progress"
        assert ProjectStatusLog.objects.count() == 1

    def test_transition_to_invalid(self, project):
        result = project.transition_to("completed")
        assert result is False
        assert project.status == "draft"

    def test_progress_percentage_no_tasks(self, project):
        assert project.progress_percentage == 0

    def test_progress_percentage_with_tasks(self, project):
        Task.objects.create(title="Task 1", project=project, is_completed=True)
        Task.objects.create(title="Task 2", project=project, is_completed=False)
        Task.objects.create(title="Task 3", project=project, is_completed=True)
        assert project.progress_percentage == 66  # noqa: PLR2004


class TestTaskModel:
    """Test Task model."""

    def test_str(self, project):
        task = Task.objects.create(title="Test Task", project=project)
        assert str(task) == f"Test Task ({project.title})"

    def test_completed_at_auto_set(self, project):
        task = Task.objects.create(
            title="Test Task",
            project=project,
            is_completed=True,
        )
        assert task.completed_at is not None

    def test_completed_at_cleared(self, project):
        task = Task.objects.create(
            title="Test Task",
            project=project,
            is_completed=True,
        )
        task.is_completed = False
        task.save()
        assert task.completed_at is None


class TestEnrollmentModel:
    """Test Enrollment model."""

    def test_str(self, course, student):
        enrollment = Enrollment.objects.create(student=student, course=course)
        assert str(enrollment) == f"{student} in {course}"
