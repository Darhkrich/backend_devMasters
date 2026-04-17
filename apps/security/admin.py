from django.contrib import admin
from .models import FailedLoginAttempt


@admin.register(FailedLoginAttempt)
class FailedLoginAdmin(admin.ModelAdmin):

    list_display = (
        "email",
        "ip_address",
        "attempts",
        "locked_until",
        "last_attempt",
    )

    search_fields = ("email", "ip_address")




from django.contrib import admin
from .models import BlockedIP


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "created_at", "blocked_until", "is_active")
    search_fields = ("ip_address",)
    list_filter = ("created_at", "blocked_until")

    def is_active(self, obj):
        return not obj.is_expired()

    is_active.boolean = True
    is_active.short_description = "Active Block"