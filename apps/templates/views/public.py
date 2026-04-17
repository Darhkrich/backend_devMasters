from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from ..selectors.templates_selectors import filter_templates, get_public_templates
from ..serializers import TemplateSerializer


class PublicTemplateViewSet(ReadOnlyModelViewSet):
    serializer_class = TemplateSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = get_public_templates().order_by("-created_at")
        return filter_templates(
            queryset,
            category=self.request.query_params.get("category"),
            template_type=self.request.query_params.get("type"),
            search=self.request.query_params.get("search"),
        )
