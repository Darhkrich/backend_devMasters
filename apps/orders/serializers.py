from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.clients.services import sync_client_metrics, upsert_client_profile
from apps.core.serializers import SanitizedModelSerializer
from apps.inquiries.models import Inquiry

from .models import Order, OrderActivity, OrderItem


class OrderItemSerializer(SanitizedModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "item_type", "item_id", "title", "price", "quantity", "metadata"]
        read_only_fields = ["id"]


class OrderActivitySerializer(SanitizedModelSerializer):
    class Meta:
        model = OrderActivity
        fields = ["id", "message", "created_by", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"project_details", "notes", "admin_notes"}

    items = OrderItemSerializer(many=True, required=False)
    activities = OrderActivitySerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    inquiry = serializers.PrimaryKeyRelatedField(
        queryset=Inquiry.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "reference",
            "user",
            "client",
            "inquiry",
            "client_name",
            "client_email",
            "client_company",
            "project_details",
            "timeline",
            "budget_min",
            "budget_max",
            "total_amount",
            "currency",
            "status",
            "notes",
            "admin_notes",
            "metadata",
            "created_at",
            "updated_at",
            "items",
            "activities",
            "item_count",
        ]
        read_only_fields = ["id", "reference", "user", "client", "created_at", "updated_at"]
        extra_kwargs = {
            "client_name": {"required": False},
            "client_email": {"required": False},
            "client_company": {"required": False},
            "project_details": {"required": False},
            "timeline": {"required": False},
            "budget_min": {"required": False},
            "budget_max": {"required": False},
            "total_amount": {"required": False},
            "currency": {"required": False},
            "notes": {"required": False},
            "admin_notes": {"required": False},
            "metadata": {"required": False},
        }

    def get_item_count(self, obj):
        return obj.items.count()

    def validate(self, attrs):
        client_email = attrs.get("client_email")
        if self.instance is None and not client_email and not attrs.get("inquiry"):
            raise serializers.ValidationError(
                {"client_email": "client_email is required when no inquiry is provided."}
            )
        return attrs

    def _build_items_from_inquiry(self, inquiry):
        if inquiry is None:
            return []

        items = []
        for item in inquiry.items.all():
            items.append(
                {
                    "item_type": item.item_type,
                    "item_id": item.item_id,
                    "title": item.title,
                    "price": item.price,
                    "quantity": item.quantity,
                    "metadata": item.metadata,
                }
            )
        return items

    def _calculate_total(self, items_data):
        total = Decimal("0.00")
        for item_data in items_data:
            price = item_data.get("price")
            quantity = item_data.get("quantity", 1) or 1
            if price is not None:
                total += Decimal(price) * Decimal(quantity)
        return total

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        inquiry = validated_data.get("inquiry")
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        if inquiry is not None:
            validated_data.setdefault("client_name", inquiry.name)
            validated_data.setdefault("client_email", inquiry.email)
            validated_data.setdefault("client_company", inquiry.company)
            validated_data.setdefault("project_details", inquiry.project_details or inquiry.message)
            validated_data.setdefault("timeline", inquiry.timeline)
            validated_data.setdefault("notes", inquiry.message)
            if not items_data:
                items_data = self._build_items_from_inquiry(inquiry)

        client = upsert_client_profile(
            name=validated_data.get("client_name", ""),
            email=validated_data.get("client_email", ""),
            phone=getattr(inquiry, "phone", ""),
            company=validated_data.get("client_company", ""),
        )
        if client is not None:
            validated_data["client"] = client

        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        if order.total_amount is None:
            order.total_amount = self._calculate_total(items_data)
            order.save(update_fields=["total_amount", "updated_at"])

        if inquiry is not None and inquiry.status != Inquiry.STATUS_RESOLVED:
            inquiry.status = Inquiry.STATUS_RESOLVED
            inquiry.save(update_fields=["status", "updated_at"])

        OrderActivity.objects.create(
            order=order,
            message="Order created",
            created_by=request.user if request and request.user.is_authenticated else None,
        )
        sync_client_metrics(client)
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        request = self.context.get("request")

        previous_status = instance.status
        previous_total = instance.total_amount
        previous_admin_notes = instance.admin_notes

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        client = upsert_client_profile(
            name=validated_data.get("client_name", instance.client_name),
            email=validated_data.get("client_email", instance.client_email),
            phone=getattr(instance.inquiry, "phone", "") if instance.inquiry else "",
            company=validated_data.get("client_company", instance.client_company),
        )
        if client is not None:
            instance.client = client

        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
            if "total_amount" not in validated_data:
                recalculated_total = self._calculate_total(items_data)
                instance.total_amount = recalculated_total
                instance.save(update_fields=["total_amount", "updated_at"])

        actor = request.user if request and request.user.is_authenticated else None
        if previous_status != instance.status:
            OrderActivity.objects.create(
                order=instance,
                message=f"Status changed from {previous_status} to {instance.status}",
                created_by=actor,
            )
        if previous_total != instance.total_amount:
            OrderActivity.objects.create(
                order=instance,
                message="Order total updated",
                created_by=actor,
            )
        if previous_admin_notes != instance.admin_notes and instance.admin_notes:
            OrderActivity.objects.create(
                order=instance,
                message="Admin notes updated",
                created_by=actor,
            )

        sync_client_metrics(client or instance.client)
        return instance


class OrderListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "reference",
            "client_name",
            "client_email",
            "client_company",
            "status",
            "total_amount",
            "currency",
            "created_at",
            "item_count",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class OrderCreateSerializer(OrderSerializer):
    class Meta(OrderSerializer.Meta):
        fields = [
            "id",
            "reference",
            "client_name",
            "client_email",
            "client_company",
            "project_details",
            "timeline",
            "budget_min",
            "budget_max",
            "currency",
            "notes",
            "metadata",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = ["id", "reference", "created_at", "updated_at"]
