import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import salted_hmac

from apps.core.models import BaseModel


ROLE_CHOICES = [
    ("ADMIN", "Admin"),
    ("USER", "User"),
    ("MODERATOR", "Moderator"),
]

STAFF_TEAM_CHOICES = [
    ("DESIGN", "Design"),
    ("DEVELOPMENT", "Development"),
    ("QA", "Quality Assurance"),
    ("DEVOPS", "DevOps"),
    ("PROJECT", "Project Management"),
    ("PRODUCT", "Product"),
    ("CONTENT", "Content"),
    ("OPERATIONS", "Operations"),
    ("OTHER", "Other"),
]


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="USER")
    staff_team = models.CharField(max_length=32, choices=STAFF_TEAM_CHOICES, blank=True, default="")
    staff_title = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    timezone = models.CharField(max_length=64, blank=True, default="UTC")
    language = models.CharField(max_length=16, blank=True, default="en")
    date_format = models.CharField(max_length=32, blank=True, default="MM/DD/YYYY")
    login_notifications_enabled = models.BooleanField(default=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
    
    def can_login(self):
        if self.is_superuser:
            return True
        return self.is_active and self.email_verified

    @property
    def can_manage_staff_workspace(self):
        return bool(
            self.is_superuser
            or (
                self.is_staff
                and (
                    self.role == "ADMIN"
                    or not self.staff_team
                )
            )
        )

    @property
    def workspace_name(self):
        if self.can_manage_staff_workspace:
            return "Admin Control Center"

        team_workspace_names = {
            "DESIGN": "Designer Workspace",
            "DEVELOPMENT": "Developer Workspace",
            "QA": "QA Workspace",
            "DEVOPS": "DevOps Workspace",
            "PROJECT": "Project Workspace",
            "PRODUCT": "Product Workspace",
            "CONTENT": "Content Workspace",
            "OPERATIONS": "Operations Workspace",
            "OTHER": "Staff Workspace",
        }
        return team_workspace_names.get(self.staff_team or "", "Staff Workspace")


class LoginHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_history",
    )
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class DeviceSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_sessions",
    )
    device = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(db_index=True)
    refresh_token = models.TextField(blank=True, default="")
    refresh_token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    refresh_token_last4 = models.CharField(max_length=4, blank=True)
    token_family = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    last_rotated_at = models.DateTimeField(null=True, blank=True)
    trusted_at = models.DateTimeField(null=True, blank=True)
    trusted_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    revoked_reason = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-last_used"]

    def __str__(self):
        return f"{self.user.email} - {self.device}"

    @staticmethod
    def build_refresh_token_hash(token):
        return salted_hmac(
            "device-session-refresh-token",
            token,
            secret=settings.SECRET_KEY,
            algorithm="sha256",
        ).hexdigest()

    def set_refresh_token(self, token):
        self.refresh_token = ""
        self.refresh_token_hash = self.build_refresh_token_hash(token)
        self.refresh_token_last4 = token[-4:]

    def matches_refresh_token(self, token):
        if not self.refresh_token_hash:
            return False
        return self.refresh_token_hash == self.build_refresh_token_hash(token)

    def mark_trusted(self, days=None):
        trust_days = days or getattr(settings, "DEVICE_TRUST_DAYS", 30)
        now = timezone.now()
        self.trusted_at = now
        self.trusted_until = now + timedelta(days=trust_days)

    def revoke(self, reason="Session revoked"):
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoked_reason = reason

    @property
    def is_trusted(self):
        return bool(self.trusted_until and self.trusted_until > timezone.now())


class LoginAttempt(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.ip_address} - {self.success}"


class FailedLoginAttempt(models.Model):
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def __str__(self):
        return f"{self.email} - {self.attempts} attempts"


class SecurityEvent(models.Model):
    EVENT_TYPES = [
        ("LOGIN_SUCCESS", "Login Success"),
        ("LOGIN_FAILED", "Login Failed"),
        ("PASSWORD_CHANGED", "Password Changed"),
        ("PASSWORD_RESET_REQUESTED", "Password Reset Requested"),
        ("PASSWORD_RESET_COMPLETED", "Password Reset Completed"),
        ("PASSWORD_RESET_FAILED", "Password Reset Failed"),
        ("EMAIL_CHANGED", "Email Changed"),
        ("2FA_ENABLED", "2FA Enabled"),
        ("2FA_DISABLED", "2FA Disabled"),
        ("2FA_FAILED", "2FA Failed"),
        ("SESSION_REVOKED", "Session Revoked"),
        ("TOKEN_REFRESHED", "Token Refreshed"),
        ("ACCOUNT_LOCKED", "Account Locked"),
        ("ADMIN_ACCESS", "Admin Access"),
        ("DATA_EXPORT", "Data Export"),
        ("DATA_DELETION", "Data Deletion"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} - {self.user}"
