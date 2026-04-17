
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.core.permissions import IsAdminUserCustom
from .models import Automation, Bundle
from .serializers import AutomationSerializer, BundleSerializer

class AutomationViewSet(ReadOnlyModelViewSet):
    queryset = Automation.objects.all().order_by('-created_at')
    serializer_class = AutomationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        sector = self.request.query_params.get('sector')
        if sector and sector != 'all':
            queryset = queryset.filter(sector=sector)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BundleViewSet(ReadOnlyModelViewSet):
    queryset = Bundle.objects.all().order_by('-created_at')
    serializer_class = BundleSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    


# automation/views.py
from rest_framework.viewsets import ModelViewSet
from .models import Automation, Bundle
from .serializers import AutomationSerializer, BundleSerializer

class AutomationAdminViewSet(ModelViewSet):
    queryset = Automation.objects.all()
    serializer_class = AutomationSerializer
    permission_classes = [IsAdminUserCustom]

class BundleAdminViewSet(ModelViewSet):
    queryset = Bundle.objects.all()
    serializer_class = BundleSerializer
    permission_classes = [IsAdminUserCustom]
