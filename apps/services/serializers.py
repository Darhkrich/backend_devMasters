from apps.core.serializers import SanitizedModelSerializer

from .models import AppService


class AppServiceSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = AppService
        fields = "__all__"
