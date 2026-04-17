from django.contrib import admin

from .models import StaffTask, StaffTaskActivity


@admin.register(StaffTask)
class StaffTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "assigned_to", "status", "priority", "due_at")
    list_filter = ("team", "status", "priority")
    search_fields = ("title", "description", "assigned_to__email")


@admin.register(StaffTaskActivity)
class StaffTaskActivityAdmin(admin.ModelAdmin):
    list_display = ("task", "event_type", "actor", "created_at")
    list_filter = ("event_type",)
    search_fields = ("task__title", "message", "actor__email")
