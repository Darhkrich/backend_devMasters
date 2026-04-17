from django.urls import path
from .views import AuditLogsView

urlpatterns = [
    path("", AuditLogsView.as_view(), name="audit-logs"),
]