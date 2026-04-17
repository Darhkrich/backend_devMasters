from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.users.models import STAFF_TEAM_CHOICES


class StaffTask(BaseModel):
    STATUS_TODO = "todo"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_IN_REVIEW = "in_review"
    STATUS_BLOCKED = "blocked"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_TODO, "To Do"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_IN_REVIEW, "In Review"),
        (STATUS_BLOCKED, "Blocked"),
        (STATUS_DONE, "Done"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CRITICAL = "critical"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_CRITICAL, "Critical"),
    ]

    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    team = models.CharField(max_length=32, choices=STAFF_TEAM_CHOICES, blank=True, default="", db_index=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_staff_tasks",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_staff_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO, db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM, db_index=True)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.PositiveSmallIntegerField(null=True, blank=True)
    acceptance_criteria = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    staff_notes = models.TextField(blank=True)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_tasks",
    )
    inquiry = models.ForeignKey(
        "inquiries.Inquiry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_tasks",
    )
    support_ticket = models.ForeignKey(
        "support.SupportTicket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_tasks",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["is_deleted", "due_at", "-created_at"]
        indexes = [
            models.Index(fields=["team", "status"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["priority", "due_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.assigned_to and not self.assigned_to.is_staff:
            raise ValidationError("Tasks can only be assigned to staff users.")
        if not self.team and self.assigned_to and self.assigned_to.staff_team:
            self.team = self.assigned_to.staff_team
        if not self.team and not self.assigned_to:
            raise ValidationError("Provide a team or assign the task to a staff user.")

    def save(self, *args, **kwargs):
        now = timezone.now()
        self.progress_percent = max(0, min(100, self.progress_percent or 0))

        if not self.team and self.assigned_to and self.assigned_to.staff_team:
            self.team = self.assigned_to.staff_team

        if self.status == self.STATUS_DONE or self.progress_percent == 100:
            self.status = self.STATUS_DONE
            self.progress_percent = 100
            if not self.completed_at:
                self.completed_at = now
        elif self.completed_at:
            self.completed_at = None

        if self.status == self.STATUS_IN_PROGRESS and not self.started_at:
            self.started_at = now

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return bool(
            self.due_at
            and self.due_at < timezone.now()
            and self.status != self.STATUS_DONE
            and not self.is_deleted
        )


class StaffTaskActivity(models.Model):
    EVENT_CREATED = "created"
    EVENT_UPDATED = "updated"
    EVENT_ASSIGNED = "assigned"
    EVENT_STATUS = "status"
    EVENT_PROGRESS = "progress"
    EVENT_NOTE = "note"
    EVENT_CHOICES = [
        (EVENT_CREATED, "Created"),
        (EVENT_UPDATED, "Updated"),
        (EVENT_ASSIGNED, "Assigned"),
        (EVENT_STATUS, "Status Changed"),
        (EVENT_PROGRESS, "Progress Changed"),
        (EVENT_NOTE, "Note Added"),
    ]

    task = models.ForeignKey(StaffTask, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_task_activities",
    )
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, default=EVENT_UPDATED)
    message = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
