from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from apps.core.permissions import IsAdminUserCustom

from .models import Package, BuilderOption, BuilderPriority
from .serializers import (
    PackageSerializer,
    BuilderOptionSerializer,
    BuilderPrioritySerializer,
)


# ========== Public grouped endpoints ==========

class PricingAPIView(APIView):
    """Returns packages grouped as the frontend expects (websites ready/custom, apps, ai)."""
    permission_classes = [AllowAny]

    def get(self, request):
        packages = Package.objects.all()
        serializer = PackageSerializer(packages, many=True)
        data = serializer.data

        result = {
            "websites": {"ready": [], "custom": []},
            "apps": [],
            "ai": []
        }

        for item in data:
            category = item['category']
            subcategory = item.get('subcategory')
            if category == 'websites':
                if subcategory == 'ready-made':
                    result['websites']['ready'].append(item)
                elif subcategory == 'custom':
                    result['websites']['custom'].append(item)
            elif category == 'apps':
                result['apps'].append(item)
            elif category == 'ai':
                result['ai'].append(item)

        return Response(result)


class BuilderViewSet(ReadOnlyModelViewSet):
    """Public builder options (grouped by type and option_type)."""
    queryset = BuilderOption.objects.all()
    serializer_class = BuilderOptionSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"], url_path="grouped")
    def grouped(self, request):
        data = {
            "web": {
                "base": BuilderOptionSerializer(
                    BuilderOption.objects.filter(type="web", option_type="base"),
                    many=True,
                ).data,
                "extras": BuilderOptionSerializer(
                    BuilderOption.objects.filter(type="web", option_type="extra"),
                    many=True,
                ).data,
            },
            "app": {
                "base": BuilderOptionSerializer(
                    BuilderOption.objects.filter(type="app", option_type="base"),
                    many=True,
                ).data,
                "extras": BuilderOptionSerializer(
                    BuilderOption.objects.filter(type="app", option_type="extra"),
                    many=True,
                ).data,
            },
            "ai": {
                "base": BuilderOptionSerializer(
                    BuilderOption.objects.filter(type="ai", option_type="base"),
                    many=True,
                ).data,
                "extras": BuilderOptionSerializer(
                    BuilderOption.objects.filter(type="ai", option_type="extra"),
                    many=True,
                ).data,
            },
            "priority": BuilderPrioritySerializer(BuilderPriority.objects.all(), many=True).data,
        }
        return Response(data)


class CalculatePriceView(APIView):
    """Calculate total price for a custom build."""
    permission_classes = [AllowAny]

    def post(self, request):
        base_id = request.data.get("base_id")
        extras = request.data.get("extras", [])
        priority_value = request.data.get("priority")
        quantity = max(int(request.data.get("quantity", 1) or 1), 1)

        subtotal = Decimal("0.00")
        line_items = []

        base = BuilderOption.objects.filter(value=base_id, option_type="base").first()
        if base:
            subtotal += base.price
            line_items.append({
                "type": "base",
                "value": base.value,
                "label": base.label,
                "price": float(base.price),
            })

        for extra in extras:
            opt = BuilderOption.objects.filter(value=extra, option_type="extra").first()
            if opt:
                subtotal += opt.price
                line_items.append({
                    "type": "extra",
                    "value": opt.value,
                    "label": opt.label,
                    "price": float(opt.price),
                })

        priority = BuilderPriority.objects.filter(value=priority_value).first()
        multiplier = priority.multiplier if priority else Decimal("1.00")
        total = (subtotal * multiplier * quantity).quantize(Decimal("0.01"))

        return Response({
            "currency": "USD",
            "subtotal": float(subtotal),
            "priority_multiplier": float(multiplier),
            "quantity": quantity,
            "total_price": float(total),
            "line_items": line_items,
        })


# ========== Admin CRUD viewsets ==========

class PackageAdminViewSet(ModelViewSet):
    """Full CRUD for packages (admin only)."""
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAdminUserCustom]


class BuilderOptionAdminViewSet(ModelViewSet):
    """Full CRUD for builder options (admin only)."""
    queryset = BuilderOption.objects.all()
    serializer_class = BuilderOptionSerializer
    permission_classes = [IsAdminUserCustom]


class BuilderPriorityAdminViewSet(ModelViewSet):
    """Full CRUD for builder priorities (admin only)."""
    queryset = BuilderPriority.objects.all()
    serializer_class = BuilderPrioritySerializer
    permission_classes = [IsAdminUserCustom]
