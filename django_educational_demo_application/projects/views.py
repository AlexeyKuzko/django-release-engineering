"""Views for educational project management."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import View

from .forms import CourseForm
from .forms import ProjectForm
from .forms import ProjectStatusTransitionForm
from .forms import TaskForm
from .models import Course
from .models import Project
from .models import Student
from .models import Task


class CourseListView(LoginRequiredMixin, ListView):
    """List all courses."""

    model = Course
    template_name = "projects/course_list.html"
    context_object_name = "courses"
    paginate_by = 10

    def get_queryset(self):
        """Filter courses by active status if requested."""
        queryset = Course.objects.annotate(
            project_count=Count("projects"),
            student_count=Count("enrollments"),
        )
        if self.request.GET.get("active_only"):
            queryset = queryset.filter(is_active=True)
        return queryset


class CourseDetailView(LoginRequiredMixin, DetailView):
    """Display course details with projects and students."""

    model = Course
    template_name = "projects/course_detail.html"
    context_object_name = "course"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        # Get projects for this course
        projects = (
            Project.objects.filter(course=course)
            .select_related("student__user")
            .order_by("-created_at")
        )

        # Get enrollments
        enrollments = course.enrollments.select_related("student__user").all()

        # Calculate statistics
        stats = {
            "total_projects": projects.count(),
            "completed_projects": projects.filter(status="completed").count(),
            "in_progress_projects": projects.filter(status="in_progress").count(),
            "average_score": projects.filter(score__isnull=False).aggregate(
                Avg("score"),
            )["score__avg"]
            or 0,
        }

        context.update(
            {
                "projects": projects,
                "enrollments": enrollments,
                "stats": stats,
            },
        )
        return context


class CourseCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new course."""

    model = Course
    form_class = CourseForm
    template_name = "projects/course_form.html"
    success_message = "Course created successfully!"

    def get_success_url(self):
        return reverse("projects:course_detail", kwargs={"pk": self.object.pk})


class CourseUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update an existing course."""

    model = Course
    form_class = CourseForm
    template_name = "projects/course_form.html"
    success_message = "Course updated successfully!"

    def get_success_url(self):
        return reverse("projects:course_detail", kwargs={"pk": self.object.pk})


class CourseDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete a course."""

    model = Course
    template_name = "projects/course_confirm_delete.html"
    success_url = reverse_lazy("projects:course_list")
    success_message = "Course deleted successfully!"


class StudentListView(LoginRequiredMixin, ListView):
    """List all students."""

    model = Student
    template_name = "projects/student_list.html"
    context_object_name = "students"
    paginate_by = 20

    def get_queryset(self):
        """Filter and annotate students."""
        queryset = Student.objects.select_related("user").annotate(
            project_count=Count("projects"),
            completed_count=Count("projects", filter=Q(projects__status="completed")),
        )

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search)
                | Q(student_id__icontains=search)
                | Q(group__icontains=search),
            )

        return queryset


class StudentDetailView(LoginRequiredMixin, DetailView):
    """Display student details with their projects."""

    model = Student
    template_name = "projects/student_detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        projects = (
            Project.objects.filter(student=student)
            .select_related("course")
            .order_by("-created_at")
        )

        enrollments = student.enrollments.select_related("course").all()

        context.update(
            {
                "projects": projects,
                "enrollments": enrollments,
                "average_score": student.get_average_score(),
            },
        )
        return context


class ProjectListView(LoginRequiredMixin, ListView):
    """List all projects with filtering."""

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 15

    def get_queryset(self):
        """Filter projects based on query parameters."""
        queryset = Project.objects.select_related(
            "student__user",
            "course",
        ).prefetch_related("tasks")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by course
        course_id = self.request.GET.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Filter by student
        student_id = self.request.GET.get("student")
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Search by title
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        # Filter overdue
        if self.request.GET.get("overdue"):
            queryset = queryset.filter(
                deadline__lt=timezone.now().date(),
                status__in=["draft", "in_progress", "review"],
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = Course.objects.filter(is_active=True)
        context["students"] = Student.objects.all()
        context["statuses"] = Project.STATUS_CHOICES
        context["priorities"] = Project.PRIORITY_CHOICES
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """Display project details with tasks and status history."""

    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        # Get tasks
        tasks = project.tasks.all()

        # Get status logs
        status_logs = project.status_logs.select_related("changed_by").all()[:10]

        # Get allowed transitions
        allowed_transitions = [
            (status, label)
            for status, label in Project.STATUS_CHOICES
            if project.can_transition_to(status)
        ]

        context.update(
            {
                "tasks": tasks,
                "status_logs": status_logs,
                "allowed_transitions": allowed_transitions,
                "transition_form": ProjectStatusTransitionForm(project=project),
                "task_form": TaskForm(),
            },
        )
        return context


class ProjectCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_message = "Project created successfully!"

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        """Set default values before saving."""
        response = super().form_valid(form)
        # Create initial status log
        project_status_log_model = self.model.status_logs.rel.related_model
        project_status_log_model.objects.create(
            project=self.object,
            old_status="draft",
            new_status=self.object.status,
            changed_by=self.request.user,
            comment="Project created",
        )
        return response


class ProjectUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"
    success_message = "Project updated successfully!"

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "projects/project_confirm_delete.html"
    success_url = reverse_lazy("projects:project_list")
    success_message = "Project deleted successfully!"


class ProjectStatusTransitionView(LoginRequiredMixin, View):
    """Handle project status transition."""

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectStatusTransitionForm(request.POST, project=project)

        if form.is_valid():
            new_status = form.cleaned_data["new_status"]
            comment = form.cleaned_data.get("comment", "")

            if project.transition_to(new_status, user=request.user):
                # Update comment if provided
                if comment:
                    log = project.status_logs.first()
                    log.comment = comment
                    log.save()

                return JsonResponse({"success": True, "status": new_status})

        return JsonResponse(
            {"success": False, "errors": form.errors},
            status=400,
        )


class TaskCreateView(LoginRequiredMixin, View):
    """Create a new task for a project."""

    def post(self, request, project_pk):
        project = get_object_or_404(Project, pk=project_pk)
        form = TaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            if not task.order:
                task.order = project.tasks.count() + 1
            task.save()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "task_id": task.id,
                        "title": task.title,
                    },
                )

            return reverse("projects:project_detail", kwargs={"pk": project_pk})

        return JsonResponse({"success": False, "errors": form.errors}, status=400)


class TaskUpdateView(LoginRequiredMixin, View):
    """Update task completion status."""

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task.is_completed = not task.is_completed
        task.save()

        return JsonResponse(
            {
                "success": True,
                "is_completed": task.is_completed,
                "completed_at": str(task.completed_at) if task.completed_at else None,
            },
        )


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a task."""

    model = Task

    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        project_pk = task.project.pk
        task.delete()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return reverse("projects:project_detail", kwargs={"pk": project_pk})


class DashboardView(LoginRequiredMixin, View):
    """Main dashboard showing project statistics."""

    template_name = "projects/dashboard.html"

    def get(self, request):
        # Overall statistics
        total_projects = Project.objects.count()
        completed_projects = Project.objects.filter(status="completed").count()
        in_progress_projects = Project.objects.filter(status="in_progress").count()
        overdue_projects = Project.objects.filter(
            deadline__lt=timezone.now().date(),
            status__in=["draft", "in_progress", "review"],
        ).count()

        # By course
        course_stats = (
            Course.objects.annotate(
                project_count=Count("projects"),
                completed_count=Count(
                    "projects",
                    filter=Q(projects__status="completed"),
                ),
                avg_score=Avg("projects__score"),
            )
            .filter(is_active=True)
            .order_by("-start_date")[:5]
        )

        # Recent projects
        recent_projects = Project.objects.select_related(
            "student__user",
            "course",
        ).order_by("-created_at")[:5]

        # Top students by average score
        top_students = (
            Student.objects.annotate(
                avg_score=Avg("projects__score"),
                project_count=Count("projects"),
            )
            .filter(projects__score__isnull=False)
            .order_by("-avg_score")[:5]
        )

        context = {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "in_progress_projects": in_progress_projects,
            "overdue_projects": overdue_projects,
            "course_stats": course_stats,
            "recent_projects": recent_projects,
            "top_students": top_students,
        }

        return render(request, self.template_name, context)
