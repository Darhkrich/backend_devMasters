from apps.core.serializers import SanitizedModelSerializer
from .models import Automation, Bundle

class AutomationSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = Automation
        fields = "__all__"

class BundleSerializer(SanitizedModelSerializer):
    multiline_sanitize_fields = {"description"}

    class Meta:
        model = Bundle
        fields = "__all__"