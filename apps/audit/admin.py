from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "action",
        "model_name",
        "method",
        "path",
        "status_code",
        "response_time",
        "timestamp",
    )

    list_filter = (
        "action",
        "method",
        "status_code",
        "timestamp",
    )

    search_fields = (
        "user__username",
        "path",
        "model_name",
    )

    readonly_fields = [field.name for field in AuditLog._meta.fields]

    ordering = ("-timestamp",)