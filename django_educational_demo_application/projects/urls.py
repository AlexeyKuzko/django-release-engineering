"""URL configuration for educational project management."""

from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),
    # Courses
    path("courses/", views.CourseListView.as_view(), name="course_list"),
    path("courses/create/", views.CourseCreateView.as_view(), name="course_create"),
    path(
        "courses/<int:pk>/",
        views.CourseDetailView.as_view(),
        name="course_detail",
    ),
    path(
        "courses/<int:pk>/update/",
        views.CourseUpdateView.as_view(),
        name="course_update",
    ),
    path(
        "courses/<int:pk>/delete/",
        views.CourseDeleteView.as_view(),
        name="course_delete",
    ),
    # Students
    path("students/", views.StudentListView.as_view(), name="student_list"),
    path(
        "students/<int:pk>/",
        views.StudentDetailView.as_view(),
        name="student_detail",
    ),
    # Projects
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path(
        "projects/create/",
        views.ProjectCreateView.as_view(),
        name="project_create",
    ),
    path(
        "projects/<int:pk>/",
        views.ProjectDetailView.as_view(),
        name="project_detail",
    ),
    path(
        "projects/<int:pk>/update/",
        views.ProjectUpdateView.as_view(),
        name="project_update",
    ),
    path(
        "projects/<int:pk>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path(
        "projects/<int:pk>/transition/",
        views.ProjectStatusTransitionView.as_view(),
        name="project_transition",
    ),
    # Tasks
    path(
        "projects/<int:project_pk>/tasks/create/",
        views.TaskCreateView.as_view(),
        name="task_create",
    ),
    path("tasks/<int:pk>/update/", views.TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
]
