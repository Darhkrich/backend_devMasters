from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdminUserCustom

from ..selectors.templates_selectors import filter_templates, get_admin_templates
from ..serializers import TemplateSerializer


class AdminTemplateViewSet(ModelViewSet):
    serializer_class = TemplateSerializer
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = get_admin_templates().order_by("-created_at")
        return filter_templates(
            queryset,
            category=self.request.query_params.get("category"),
            template_type=self.request.query_params.get("type"),
            search=self.request.query_params.get("search"),
        )
