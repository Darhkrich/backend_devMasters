import json
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import salted_hmac


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("VIEW", "View"),
        ("REQUEST", "Request"),
        ("OTHER", "Other"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=255, blank=True, null=True)
    object_id = models.CharField(max_length=50, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True, db_index=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    previous_hash = models.CharField(max_length=64, blank=True)
    entry_hash = models.CharField(max_length=64, editable=False, db_index=True)
    retention_until = models.DateTimeField(null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} | {self.action} | {self.path}"

    def _hash_payload(self):
        payload = {
            "user_id": self.user_id,
            "action": self.action,
            "model_name": self.model_name,
            "object_id": self.object_id,
            "ip_address": self.ip_address,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "previous_hash": self.previous_hash,
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _calculate_entry_hash(self):
        secret = getattr(settings, "AUDIT_LOG_SIGNING_KEY", settings.SECRET_KEY)
        return salted_hmac(
            "audit-log-chain",
            self._hash_payload(),
            secret=secret,
            algorithm="sha256",
        ).hexdigest()

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit logs are immutable and cannot be modified.")

        if not self.timestamp:
            self.timestamp = timezone.now()

        if not self.retention_until:
            days = getattr(settings, "AUDIT_LOG_RETENTION_DAYS", 365)
            self.retention_until = self.timestamp + timedelta(days=days)

        if not self.previous_hash:
            previous = AuditLog.objects.order_by("-timestamp", "-id").first()
            self.previous_hash = previous.entry_hash if previous else ""

        self.entry_hash = self._calculate_entry_hash()
        super().save(*args, **kwargs)
