import ipaddress
from pathlib import PurePosixPath
from urllib.parse import urlparse

from django.conf import settings
from rest_framework import serializers

from apps.core.serializers import SanitizedModelSerializer

from .models import ProjectFile


def _user_can_access_order(user, order):
    if getattr(user, "can_manage_staff_workspace", False):
        return True
    return bool(
        order
        and (
            order.user_id == user.id
            or (user.email and order.client_email and order.client_email.lower() == user.email.lower())
        )
    )


def _user_can_access_inquiry(user, inquiry):
    if getattr(user, "can_manage_staff_workspace", False):
        return True
    return bool(
        inquiry
        and (
            inquiry.user_id == user.id
            or (user.email and inquiry.email and inquiry.email.lower() == user.email.lower())
        )
    )


class ProjectFileSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description", "review_notes"}
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = ProjectFile
        fields = [
            "id",
            "order",
            "inquiry",
            "uploaded_by",
            "uploader",
            "uploader_role",
            "file_name",
            "file",
            "file_url",
            "file_type",
            "size_bytes",
            "description",
            "review_status",
            "review_notes",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_uploaded_by(self, obj) -> str:
        if getattr(obj, "uploaded_by", ""):
            return obj.uploaded_by
        if obj.uploader:
            return obj.uploader.get_full_name() or obj.uploader.email
        return ""


class ProjectFileCreateSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = ProjectFile
        fields = [
            "id",
            "order",
            "inquiry",
            "file",
            "file_url",
            "description",
            "file_name",
            "file_type",
            "size_bytes",
            "created_at",
        ]
        read_only_fields = ["id", "file_name", "file_type", "size_bytes", "created_at"]

    def validate(self, attrs):
        upload = attrs.get("file")
        file_url = attrs.get("file_url", "")
        order = attrs.get("order")
        inquiry = attrs.get("inquiry")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not upload and not file_url:
            raise serializers.ValidationError("Provide either an uploaded file or a file_url.")
        if upload and file_url:
            raise serializers.ValidationError("Provide either an uploaded file or a file_url, not both.")
        if not order and not inquiry:
            raise serializers.ValidationError("Link the file to an order or an inquiry.")

        if user and user.is_authenticated and not getattr(user, "can_manage_staff_workspace", False):
            if order and not _user_can_access_order(user, order):
                raise serializers.ValidationError({"order": "You cannot upload files to this order."})
            if inquiry and not _user_can_access_inquiry(user, inquiry):
                raise serializers.ValidationError({"inquiry": "You cannot upload files to this inquiry."})

        if upload is not None:
            try:
                self._validate_upload(upload)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"file": exc.detail}) from exc
        if file_url:
            try:
                self._validate_external_url(file_url)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"file_url": exc.detail}) from exc

        return attrs

    def _validate_upload(self, upload):
        max_bytes = int(getattr(settings, "PROJECT_FILE_UPLOAD_MAX_BYTES", 0) or 0)
        if max_bytes and getattr(upload, "size", 0) > max_bytes:
            raise serializers.ValidationError(
                f"File exceeds the {max_bytes // (1024 * 1024)}MB upload limit."
            )

        file_name = PurePosixPath(upload.name).name
        suffix = PurePosixPath(file_name).suffix.lower()
        allowed_extensions = {
            extension.lower()
            for extension in getattr(settings, "PROJECT_FILE_ALLOWED_EXTENSIONS", [])
        }
        if allowed_extensions and suffix not in allowed_extensions:
            raise serializers.ValidationError("This file type is not allowed.")

        allowed_content_types = {
            content_type.lower()
            for content_type in getattr(settings, "PROJECT_FILE_ALLOWED_CONTENT_TYPES", [])
        }
        content_type = (getattr(upload, "content_type", "") or "").lower()
        if content_type and allowed_content_types and content_type not in allowed_content_types:
            raise serializers.ValidationError("This file content type is not allowed.")

    def _validate_external_url(self, value):
        parsed = urlparse(value)
        allowed_schemes = {
            scheme.lower()
            for scheme in getattr(settings, "PROJECT_FILE_ALLOWED_URL_SCHEMES", ["https"])
        }
        if parsed.scheme.lower() not in allowed_schemes:
            raise serializers.ValidationError("Only approved URL schemes are allowed.")
        if not parsed.netloc:
            raise serializers.ValidationError("Enter a valid external file URL.")

        host = (parsed.hostname or "").strip().lower()
        if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
            raise serializers.ValidationError("Local or loopback URLs are not allowed.")

        suffix = PurePosixPath(parsed.path).suffix.lower()
        allowed_extensions = {
            extension.lower()
            for extension in getattr(settings, "PROJECT_FILE_ALLOWED_EXTENSIONS", [])
        }
        if suffix and allowed_extensions and suffix not in allowed_extensions:
            raise serializers.ValidationError("This file type is not allowed.")

        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return

        if any(
            [
                address.is_private,
                address.is_loopback,
                address.is_link_local,
                address.is_multicast,
                address.is_reserved,
            ]
        ):
            raise serializers.ValidationError("Private-network URLs are not allowed.")

    def create(self, validated_data):
        upload = validated_data.get("file")
        file_url = validated_data.get("file_url", "")

        if upload is not None:
            validated_data.setdefault("file_name", PurePosixPath(upload.name).name)
            validated_data.setdefault("file_type", upload.content_type or "")
            validated_data.setdefault("size_bytes", upload.size or 0)
        elif file_url:
            validated_data.setdefault(
                "file_name",
                PurePosixPath(urlparse(file_url).path).name or "external-file",
            )

        return super().create(validated_data)


class ProjectFileClientUpdateSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = ProjectFile
        fields = ["description"]


class ProjectFileAdminUpdateSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description", "review_notes"}

    class Meta:
        model = ProjectFile
        fields = ["description", "review_status", "review_notes"]
