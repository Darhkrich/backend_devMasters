




from django.contrib import admin

from apps.core.models import TaskJob


@admin.register(TaskJob)
class TaskJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "status",
        "attempts",
        "max_attempts",
        "available_at",
        "locked_by",
        "created_at",
    )
    list_filter = ("status", "name")
    search_fields = ("name", "locked_by")
