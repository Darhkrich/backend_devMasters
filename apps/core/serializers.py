from rest_framework import serializers

from .sanitization import sanitize_structure


class SanitizedSerializerMixin:
    multiline_sanitize_fields = set()
    raw_string_fields = set()

    def to_internal_value(self, data):
        clean_data = sanitize_structure(
            data,
            multiline_fields=set(self.multiline_sanitize_fields),
            raw_fields=set(self.raw_string_fields),
        )
        return super().to_internal_value(clean_data)


class SanitizedModelSerializer(SanitizedSerializerMixin, serializers.ModelSerializer):
    pass


class SanitizedSerializer(SanitizedSerializerMixin, serializers.Serializer):
    pass
