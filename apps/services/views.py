from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.core.permissions import IsAdminUserCustom

from .models import AppService
from .serializers import AppServiceSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import AppService
from .serializers import AppServiceSerializer
# services/views.py
from rest_framework.viewsets import ModelViewSet
from .models import AppService
from .serializers import AppServiceSerializer

class AppServiceViewSet(ReadOnlyModelViewSet):
    queryset = AppService.objects.all().order_by("-created_at")
    serializer_class = AppServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()

        category = self.request.query_params.get("category")
        type_param = self.request.query_params.get("type")
        search = self.request.query_params.get("search")

        if category:
            queryset = queryset.filter(category=category)

        if type_param and type_param != "all":
            queryset = queryset.filter(type__contains=[type_param])

        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        # If flat=true is requested, return a flat array (for frontend that expects an array)
        if request.query_params.get('flat') == 'true':
            return Response(serializer.data)

        # Otherwise return the grouped structure (matching mockup)
        output = {
            "APP_SERVICES": [item for item in serializer.data if item['category'] == 'service'],
            "APP_BLUEPRINTS": [item for item in serializer.data if item['category'] == 'blueprint']
        }
        return Response(output)
    





class AppServiceAdminViewSet(ModelViewSet):
    queryset = AppService.objects.all()
    serializer_class = AppServiceSerializer
    permission_classes = [IsAdminUserCustom]
