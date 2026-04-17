from rest_framework import serializers

from apps.core.serializers import SanitizedModelSerializer

from .models import ClientProfile


class ClientProfileSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"notes"}

    inquiry_count = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    thread_count = serializers.SerializerMethodField()
    open_ticket_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "company",
            "plan",
            "credits",
            "active_projects",
            "next_billing",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
            "inquiry_count",
            "order_count",
            "thread_count",
            "open_ticket_count",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_inquiry_count(self, obj):
        return obj.inquiries.count()

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_thread_count(self, obj):
        return obj.threads.count()

    def get_open_ticket_count(self, obj):
        return obj.tickets.exclude(status="closed").count()


class ClientListSerializer(serializers.ModelSerializer):
    inquiry_count = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "name",
            "email",
            "company",
            "plan",
            "active_projects",
            "is_active",
            "created_at",
            "inquiry_count",
            "order_count",
        ]

    def get_inquiry_count(self, obj):
        return obj.inquiries.count()

    def get_order_count(self, obj):
        return obj.orders.count()
