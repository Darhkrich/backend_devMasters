from rest_framework import serializers

from apps.clients.services import upsert_client_profile
from apps.core.serializers import SanitizedModelSerializer

from .models import Inquiry, InquiryItem


class InquiryItemSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = InquiryItem
        fields = [
            "id",
            "item_type",
            "item_id",
            "title",
            "category",
            "source",
            "description",
            "price",
            "price_type",
            "quantity",
            "metadata",
        ]
        read_only_fields = ["id"]


class InquirySerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"message", "project_details", "admin_reply"}

    items = InquiryItemSerializer(many=True, required=False)
    estimated_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "user",
            "client",
            "name",
            "email",
            "company",
            "phone",
            "subject",
            "service_category",
            "timeline",
            "budget",
            "message",
            "project_details",
            "status",
            "admin_reply",
            "metadata",
            "created_at",
            "updated_at",
            "items",
            "estimated_total",
        ]
        read_only_fields = ["id", "user", "client", "created_at", "updated_at"]

    def validate(self, attrs):
        items = attrs.get("items", [])
        if not attrs.get("message") and not attrs.get("project_details") and not items:
            raise serializers.ValidationError(
                "Provide project details, a message, or at least one selected item."
            )
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data.setdefault("user", request.user)

        client = upsert_client_profile(
            name=validated_data.get("name", ""),
            email=validated_data.get("email", ""),
            phone=validated_data.get("phone", ""),
            company=validated_data.get("company", ""),
        )
        if client is not None:
            validated_data["client"] = client

        inquiry = Inquiry.objects.create(**validated_data)
        for item_data in items_data:
            InquiryItem.objects.create(inquiry=inquiry, **item_data)
        return inquiry

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        client = upsert_client_profile(
            name=validated_data.get("name", instance.name),
            email=validated_data.get("email", instance.email),
            phone=validated_data.get("phone", instance.phone),
            company=validated_data.get("company", instance.company),
        )
        if client is not None:
            instance.client = client

        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                InquiryItem.objects.create(inquiry=instance, **item_data)

        return instance


class InquiryListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    estimated_total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "name",
            "email",
            "company",
            "service_category",
            "status",
            "created_at",
            "item_count",
            "estimated_total",
        ]

    def get_item_count(self, obj):
        return obj.items.count()


class InquiryCreateSerializer(InquirySerializer):
    class Meta(InquirySerializer.Meta):
        fields = [
            "id",
            "name",
            "email",
            "company",
            "phone",
            "subject",
            "service_category",
            "timeline",
            "budget",
            "message",
            "project_details",
            "metadata",
            "created_at",
            "updated_at",
            "items",
            "estimated_total",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "estimated_total"]
