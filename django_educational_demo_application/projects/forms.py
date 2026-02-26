"""Forms for educational project management."""

from django import forms

from .models import Course
from .models import Enrollment
from .models import Project
from .models import Student
from .models import Task


class CourseForm(forms.ModelForm):
    """Form for creating and editing courses."""

    class Meta:
        model = Course
        fields = [
            "name",
            "code",
            "description",
            "start_date",
            "end_date",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self) -> dict:
        """Validate that end_date is after start_date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            msg = "End date must be after start date."
            raise forms.ValidationError(msg)

        return cleaned_data


class StudentForm(forms.ModelForm):
    """Form for creating and editing student profiles."""

    class Meta:
        model = Student
        fields = ["user", "student_id", "group"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "student_id": forms.TextInput(attrs={"class": "form-control"}),
            "group": forms.TextInput(attrs={"class": "form-control"}),
        }


class EnrollmentForm(forms.ModelForm):
    """Form for enrolling students in courses."""

    class Meta:
        model = Enrollment
        fields = ["student", "course", "is_active"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-control"}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects."""

    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "course",
            "student",
            "status",
            "priority",
            "score",
            "repository_url",
            "deployed_url",
            "deadline",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "course": forms.Select(attrs={"class": "form-control"}),
            "student": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "score": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 100},
            ),
            "repository_url": forms.URLInput(attrs={"class": "form-control"}),
            "deployed_url": forms.URLInput(attrs={"class": "form-control"}),
            "deadline": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
            ),
        }

    def clean(self) -> dict:
        """Validate project data."""
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        score = cleaned_data.get("score")

        # Score should only be set for completed projects
        if score is not None and status not in ["completed", "archived"]:
            self.add_error(
                "score",
                forms.ValidationError(
                    "Score can only be set for completed or archived projects.",
                ),
            )

        return cleaned_data


class ProjectStatusTransitionForm(forms.Form):
    """Form for transitioning project status."""

    new_status = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, *args, project: Project | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if project:
            # Filter to only allowed transitions
            allowed = [
                (status, label)
                for status, label in Project.STATUS_CHOICES
                if project.can_transition_to(status)
            ]
            self.fields["new_status"].choices = allowed


class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks."""

    class Meta:
        model = Task
        fields = ["title", "description", "order", "is_completed"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_completed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TaskBulkForm(forms.Form):
    """Form for adding multiple tasks at once."""

    titles = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Enter task titles, one per line",
            },
        ),
        help_text="Enter one task title per line",
    )
