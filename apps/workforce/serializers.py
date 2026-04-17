from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.core.serializers import SanitizedModelSerializer
from apps.inquiries.models import Inquiry
from apps.orders.models import Order
from apps.support.models import SupportTicket

from .models import StaffTask, StaffTaskActivity
from .permissions import can_manage_staff_workspace


User = get_user_model()


class TeamMemberSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    workspace_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "staff_team",
            "staff_title",
            "workspace_name",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


class TeamMemberSerializer(SanitizedModelSerializer):
    full_name = serializers.SerializerMethodField()
    can_manage_staff_workspace = serializers.SerializerMethodField()
    workspace_name = serializers.CharField(read_only=True)
    active_task_count = serializers.IntegerField(read_only=True)
    overdue_task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_staff",
            "is_active",
            "staff_team",
            "staff_title",
            "can_manage_staff_workspace",
            "workspace_name",
            "active_task_count",
            "overdue_task_count",
        ]
        read_only_fields = [
            "email",
            "role",
            "can_manage_staff_workspace",
            "workspace_name",
            "active_task_count",
            "overdue_task_count",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email

    def get_can_manage_staff_workspace(self, obj):
        return obj.can_manage_staff_workspace

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if not request or not can_manage_staff_workspace(request.user):
            raise serializers.ValidationError({"detail": "You cannot update staff members."})
        return super().update(instance, validated_data)


class StaffTaskActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffTaskActivity
        fields = ["id", "event_type", "message", "actor_name", "metadata", "created_at"]

    def get_actor_name(self, obj):
        if not obj.actor:
            return "System"
        return f"{obj.actor.first_name} {obj.actor.last_name}".strip() or obj.actor.email


class StaffTaskSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {
        "description",
        "acceptance_criteria",
        "admin_notes",
        "staff_notes",
    }

    assigned_to = TeamMemberSummarySerializer(read_only=True)
    assigned_by = TeamMemberSummarySerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source="assigned_to",
        queryset=User.objects.filter(is_staff=True, is_active=True),
        allow_null=True,
        required=False,
        write_only=True,
    )
    order_id = serializers.PrimaryKeyRelatedField(
        source="order",
        queryset=Order.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    inquiry_id = serializers.PrimaryKeyRelatedField(
        source="inquiry",
        queryset=Inquiry.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    support_ticket_id = serializers.PrimaryKeyRelatedField(
        source="support_ticket",
        queryset=SupportTicket.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    order_reference = serializers.CharField(source="order.reference", read_only=True)
    inquiry_subject = serializers.CharField(source="inquiry.subject", read_only=True)
    support_ticket_subject = serializers.CharField(source="support_ticket.subject", read_only=True)
    activities = StaffTaskActivitySerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = StaffTask
        fields = [
            "id",
            "title",
            "description",
            "team",
            "assigned_to",
            "assigned_by",
            "assigned_to_id",
            "status",
            "priority",
            "progress_percent",
            "due_at",
            "started_at",
            "completed_at",
            "estimated_hours",
            "acceptance_criteria",
            "admin_notes",
            "staff_notes",
            "order",
            "order_id",
            "order_reference",
            "inquiry",
            "inquiry_id",
            "inquiry_subject",
            "support_ticket",
            "support_ticket_id",
            "support_ticket_subject",
            "metadata",
            "is_overdue",
            "activities",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "assigned_to",
            "assigned_by",
            "order",
            "inquiry",
            "support_ticket",
            "order_reference",
            "inquiry_subject",
            "support_ticket_subject",
            "is_overdue",
            "activities",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate_progress_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress must be between 0 and 100.")
        return value

    def validate(self, attrs):
        assigned_to = attrs.get("assigned_to", getattr(self.instance, "assigned_to", None))
        team = attrs.get("team", getattr(self.instance, "team", ""))

        if assigned_to and not assigned_to.is_staff:
            raise serializers.ValidationError({"assigned_to_id": "Tasks can only be assigned to staff users."})

        if not team and assigned_to and assigned_to.staff_team:
            attrs["team"] = assigned_to.staff_team

        if not attrs.get("team", getattr(self.instance, "team", "")) and not assigned_to:
            raise serializers.ValidationError({"team": "Select a staff team or assign the task to a staff user."})

        due_at = attrs.get("due_at", getattr(self.instance, "due_at", None))
        if due_at and due_at < timezone.now() and self.instance is None:
            raise serializers.ValidationError({"due_at": "Use a current or future deadline for new tasks."})

        return attrs
