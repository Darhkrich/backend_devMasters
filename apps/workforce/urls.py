from django.urls import path

from .views import (
    StaffTaskDetailView,
    StaffTaskListView,
    TeamMemberDetailView,
    TeamMemberListView,
    WorkforceDashboardView,
)


urlpatterns = [
    path("dashboard/", WorkforceDashboardView.as_view(), name="workforce-dashboard"),
    path("team-members/", TeamMemberListView.as_view(), name="workforce-team-members"),
    path("team-members/<int:pk>/", TeamMemberDetailView.as_view(), name="workforce-team-member-detail"),
    path("tasks/", StaffTaskListView.as_view(), name="workforce-task-list"),
    path("tasks/<int:pk>/", StaffTaskDetailView.as_view(), name="workforce-task-detail"),
]
