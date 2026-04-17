from rest_framework import serializers

from apps.core.serializers import SanitizedModelSerializer, SanitizedSerializer

from .models import Message, MessageThread


class MessageSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"body"}

    class Meta:
        model = Message
        fields = ["id", "thread", "sender_name", "sender_role", "body", "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]


class MessageThreadSerializer(SanitizedModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = [
            "id",
            "client",
            "inquiry",
            "order",
            "subject",
            "is_archived",
            "unread_count",
            "last_message",
            "client_name",
            "client_email",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            sender_role = "admin"
        else:
            sender_role = "client"
        return obj.messages.filter(is_read=False, sender_role=sender_role).count()

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return {
                "sender_name": msg.sender_name,
                "body": msg.body[:80],
                "created_at": msg.created_at,
            }
        return None

    def get_client_name(self, obj):
        return getattr(obj.client, "name", "") or ""

    def get_client_email(self, obj):
        return getattr(obj.client, "email", "") or ""


class MessageThreadListSerializer(SanitizedModelSerializer):
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = [
            "id",
            "client",
            "inquiry",
            "order",
            "subject",
            "is_archived",
            "unread_count",
            "last_message",
            "message_count",
            "client_name",
            "client_email",
            "updated_at",
        ]

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_staff:
            sender_role = "admin"
        else:
            sender_role = "client"
        return obj.messages.filter(is_read=False, sender_role=sender_role).count()

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return {
                "sender_name": msg.sender_name,
                "body": msg.body[:80],
                "created_at": msg.created_at,
            }
        return None

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_client_name(self, obj):
        return getattr(obj.client, "name", "") or ""

    def get_client_email(self, obj):
        return getattr(obj.client, "email", "") or ""


class ReplySerializer(SanitizedSerializer):
    multiline_sanitize_fields = {"body"}
    sender_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    sender_role = serializers.CharField(required=False, allow_blank=True)
    body = serializers.CharField()
