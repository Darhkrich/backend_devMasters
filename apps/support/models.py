from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SupportTicket(models.Model):
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in-progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("urgent", "Urgent"),
    ]
    CATEGORY_CHOICES = [
        ("technical", "Technical Issue"),
        ("billing", "Billing"),
        ("project", "Project Related"),
        ("general", "General Enquiry"),
        ("feedback", "Feedback"),
    ]

    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_support_tickets",
    )
    guest_name = models.CharField(max_length=200, blank=True)
    guest_email = models.EmailField(blank=True)

    subject = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")
    first_response_due_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    first_responded_at = models.DateTimeField(null=True, blank=True)
    is_escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalation_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.pk} - {self.subject} ({self.status})"

    @staticmethod
    def first_response_sla_for_priority(priority):
        return {
            "low": timedelta(hours=8),
            "normal": timedelta(hours=4),
            "urgent": timedelta(hours=1),
        }.get(priority or "normal", timedelta(hours=4))

    @staticmethod
    def resolution_sla_for_priority(priority):
        return {
            "low": timedelta(days=5),
            "normal": timedelta(days=2),
            "urgent": timedelta(hours=8),
        }.get(priority or "normal", timedelta(days=2))

    def ensure_sla_deadlines(self, *, reference_time=None):
        now = reference_time or self.created_at or timezone.now()
        changed_fields = []

        if not self.first_response_due_at:
            self.first_response_due_at = now + self.first_response_sla_for_priority(self.priority)
            changed_fields.append("first_response_due_at")

        if not self.resolution_due_at:
            self.resolution_due_at = now + self.resolution_sla_for_priority(self.priority)
            changed_fields.append("resolution_due_at")

        return changed_fields

    def refresh_workflow_state(self, *, reference_time=None, save=True):
        now = reference_time or timezone.now()
        changed_fields = self.ensure_sla_deadlines(reference_time=self.created_at or now)

        first_admin_reply = self.replies.filter(sender_role="admin").first()
        if first_admin_reply and not self.first_responded_at:
            self.first_responded_at = first_admin_reply.created_at
            changed_fields.append("first_responded_at")

        if self.status in [self.STATUS_RESOLVED, self.STATUS_CLOSED]:
            if save and changed_fields:
                self.save(update_fields=[*changed_fields, "updated_at"])
            return changed_fields

        breach_reason = ""
        if not self.first_responded_at and self.first_response_due_at and now > self.first_response_due_at:
            breach_reason = "First response SLA missed"
        elif self.resolution_due_at and now > self.resolution_due_at:
            breach_reason = "Resolution SLA missed"

        if breach_reason and not self.is_escalated:
            self.is_escalated = True
            self.escalated_at = now
            self.escalation_reason = breach_reason
            changed_fields.extend(["is_escalated", "escalated_at", "escalation_reason"])

        if save and changed_fields:
            self.save(update_fields=[*changed_fields, "updated_at"])

        return changed_fields

    @property
    def sla_status(self):
        now = timezone.now()
        if self.status in [self.STATUS_RESOLVED, self.STATUS_CLOSED]:
            return "resolved"
        if self.is_escalated:
            return "escalated"
        if not self.first_responded_at and self.first_response_due_at:
            return "at_risk" if now >= self.first_response_due_at else "on_track"
        if self.resolution_due_at:
            return "at_risk" if now >= self.resolution_due_at else "on_track"
        return "on_track"

    def save(self, *args, **kwargs):
        reference_time = self.created_at or timezone.now()
        self.ensure_sla_deadlines(reference_time=reference_time)
        super().save(*args, **kwargs)


class TicketReply(models.Model):
    ROLE_CHOICES = [
        ("client", "Client"),
        ("admin", "Admin"),
    ]

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="replies")
    sender_name = models.CharField(max_length=200)
    sender_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply to Ticket #{self.ticket_id} by {self.sender_name}"
