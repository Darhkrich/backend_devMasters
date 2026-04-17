from rest_framework import serializers

from apps.core.serializers import SanitizedModelSerializer, SanitizedSerializer

from .models import SupportTicket, TicketReply


class TicketReplySerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"body"}

    class Meta:
        model = TicketReply
        fields = ["id", "ticket", "sender_name", "sender_role", "body", "created_at"]
        read_only_fields = ["id", "created_at"]


class SupportTicketSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description", "escalation_reason"}

    replies = TicketReplySerializer(many=True, read_only=True)
    client_name = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "client",
            "assigned_to",
            "guest_name",
            "guest_email",
            "subject",
            "description",
            "category",
            "status",
            "priority",
            "client_name",
            "client_email",
            "assigned_to_name",
            "assigned_to_email",
            "first_response_due_at",
            "resolution_due_at",
            "first_responded_at",
            "is_escalated",
            "escalated_at",
            "escalation_reason",
            "sla_status",
            "replies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_client_name(self, obj):
        return getattr(obj.client, "name", "") or obj.guest_name

    def get_client_email(self, obj):
        return getattr(obj.client, "email", "") or obj.guest_email

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return ""
        return obj.assigned_to.get_full_name() or obj.assigned_to.email

    def get_assigned_to_email(self, obj):
        return getattr(obj.assigned_to, "email", "") or ""

    def get_sla_status(self, obj):
        return obj.sla_status


class SupportTicketListSerializer(SanitizedModelSerializer):
    reply_count = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.SerializerMethodField()
    sla_status = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "subject",
            "category",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_name",
            "assigned_to_email",
            "guest_name",
            "guest_email",
            "client",
            "client_name",
            "client_email",
            "first_response_due_at",
            "resolution_due_at",
            "first_responded_at",
            "is_escalated",
            "escalated_at",
            "escalation_reason",
            "sla_status",
            "reply_count",
            "created_at",
            "updated_at",
        ]

    def get_reply_count(self, obj):
        return obj.replies.count()

    def get_client_name(self, obj):
        return getattr(obj.client, "name", "") or obj.guest_name

    def get_client_email(self, obj):
        return getattr(obj.client, "email", "") or obj.guest_email

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return ""
        return obj.assigned_to.get_full_name() or obj.assigned_to.email

    def get_assigned_to_email(self, obj):
        return getattr(obj.assigned_to, "email", "") or ""

    def get_sla_status(self, obj):
        return obj.sla_status


class TicketReplyCreateSerializer(SanitizedSerializer):
    multiline_sanitize_fields = {"body"}
    sender_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    sender_role = serializers.CharField(required=False, allow_blank=True)
    body = serializers.CharField()


class SupportTicketCreateSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = SupportTicket
        fields = [
            "client",
            "guest_name",
            "guest_email",
            "subject",
            "description",
            "category",
            "priority",
        ]
