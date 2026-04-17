from django.conf import settings
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_id = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.ip_address}"


class SecurityAlert(models.Model):
    SEVERITY_LEVELS = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_alerts",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_LEVELS,
        default="medium",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.severity.upper()} - {self.title}"


class FailedLoginAttempt(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def __str__(self):
        return f"{self.email} - {self.attempts} attempts"


class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255, default="Suspicious activity detected")
    created_at = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    block_count = models.PositiveIntegerField(default=0)

    def is_expired(self):
        return bool(self.blocked_until and timezone.now() > self.blocked_until)

    @property
    def is_active(self):
        return not self.is_expired()

    def __str__(self):
        return self.ip_address


class IPActivity(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    failed_logins = models.IntegerField(default=0)
    request_count = models.IntegerField(default=0)
    last_request = models.DateTimeField(auto_now=True)
    risk_score = models.FloatField(default=0)

    def __str__(self):
        return self.ip_address



# apps/security/models.py

class TrustedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ip_address


class SuspiciousIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    failed_logins = models.IntegerField(default=0)
    risk_score = models.FloatField(default=0)
    request_count = models.IntegerField(default=0)
    block_count = models.PositiveIntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    last_success = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ip_address


class KnownDevice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="known_devices",
    )
    device = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "device")

    def __str__(self):
        return f"{self.user} - {self.device}"


