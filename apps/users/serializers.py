import uuid
from zoneinfo import available_timezones

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from rest_framework import serializers
from apps.core.serializers import SanitizedModelSerializer, SanitizedSerializer

from .models import DeviceSession, LoginHistory, SecurityEvent


User = get_user_model()


class UserSerializer(SanitizedModelSerializer):
    can_manage_staff_workspace = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "bio",
            "timezone",
            "language",
            "date_format",
            "login_notifications_enabled",
            "notification_preferences",
            "role",
            "staff_team",
            "staff_title",
            "email_verified",
            "is_staff",
            "is_superuser",
            "is_active",
            "account_locked_until",
            "can_manage_staff_workspace",
            "workspace_name",
        ]
        read_only_fields = [
            "is_superuser",
            "account_locked_until",
            "email_verified",
            "can_manage_staff_workspace",
            "workspace_name",
        ]

    def get_can_manage_staff_workspace(self, obj):
        return obj.can_manage_staff_workspace

    def get_workspace_name(self, obj):
        return obj.workspace_name

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if not request or not request.user.is_staff:
            for field in (
                "is_staff",
                "is_superuser",
                "is_active",
                "role",
                "staff_team",
                "staff_title",
                "account_locked_until",
            ):
                validated_data.pop(field, None)

        return super().update(instance, validated_data)


class RegisterSerializer(SanitizedModelSerializer):
    raw_string_fields = {"password"}
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "password")

    def validate_email(self, value):
        return value.lower().strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        first_name = validated_data["first_name"].strip()
        last_name = validated_data["last_name"].strip()
        email = validated_data["email"]
        password = validated_data["password"]
        username = validated_data.get("username", "").strip()

        if not username:
            username = slugify(f"{first_name}{last_name}-{uuid.uuid4().hex[:6]}")

        return User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )


class LoginSerializer(SanitizedSerializer):
    raw_string_fields = {"password"}
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower().strip()


class ForgotPasswordSerializer(SanitizedSerializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class ResetPasswordSerializer(SanitizedSerializer):
    raw_string_fields = {"uid", "token", "new_password"}
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class UserProfileSerializer(SanitizedModelSerializer):
    two_factor_auth_enabled = serializers.BooleanField(source="two_factor_enabled", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "bio",
            "timezone",
            "language",
            "date_format",
            "login_notifications_enabled",
            "notification_preferences",
            "two_factor_auth_enabled",
            "email_verified",
        ]
        read_only_fields = ["email", "email_verified"]

    def validate_phone(self, value):
        return value.strip()

    def validate_bio(self, value):
        return value.strip()

    def validate_timezone(self, value):
        value = value.strip() or "UTC"
        if value not in available_timezones():
            raise serializers.ValidationError("Select a valid timezone.")
        return value

    def validate_language(self, value):
        return value.strip().lower() or "en"

    def validate_date_format(self, value):
        value = value.strip() or "MM/DD/YYYY"
        allowed_formats = {"MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"}
        if value not in allowed_formats:
            raise serializers.ValidationError("Select a supported date format.")
        return value

    def validate_notification_preferences(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Notification preferences must be an object.")

        normalized = {}
        for key, preference in value.items():
            normalized[str(key).strip().lower()] = bool(preference)
        return normalized


class ChangePasswordSerializer(SanitizedSerializer):
    raw_string_fields = {"old_password", "new_password"}
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangeEmailSerializer(SanitizedSerializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        return value.lower().strip()


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = ["id", "ip_address", "user_agent", "created_at"]


class DeviceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceSession
        fields = [
            "id",
            "device",
            "ip_address",
            "created_at",
            "last_used",
            "trusted_until",
            "expires_at",
            "revoked_at",
            "is_active",
        ]


class SecurityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityEvent
        fields = [
            "event_type",
            "ip_address",
            "user_agent",
            "metadata",
            "created_at",
        ]
