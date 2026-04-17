from rest_framework import serializers
from apps.core.serializers import SanitizedModelSerializer
from .models import Template
import json


class TemplateSerializer(SanitizedModelSerializer):
    # Override category field to handle JSON string conversion
    category = serializers.JSONField(required=False)
    tags = serializers.JSONField(required=False)
    icons = serializers.JSONField(required=False)

    class Meta:
        model = Template
        fields = "__all__"

    def to_internal_value(self, data):
        # Convert JSON string to list for JSON fields
        for field in ['category', 'tags', 'icons']:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    raise serializers.ValidationError({field: 'Invalid JSON format.'})
        return super().to_internal_value(data)

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Template name is too short.")
        return value

    def validate_category(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Category must be a list.")
        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Each category must be a string.")
        return value

    def validate(self, data):
        instance = getattr(self, "instance", None)
        preview_url = data.get("preview_url", getattr(instance, "preview_url", ""))
        image = data.get("image", getattr(instance, "image", None))
        if not preview_url and not image:
            raise serializers.ValidationError(
                {"preview_url": "Provide a preview_url or upload an image."}
            )
        return data