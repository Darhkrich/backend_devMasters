from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PricingAPIView,
    BuilderViewSet,
    CalculatePriceView,
    PackageAdminViewSet,
    BuilderOptionAdminViewSet,
    BuilderPriorityAdminViewSet,
)

router = DefaultRouter()
router.register(r'builder', BuilderViewSet, basename='builder')

urlpatterns = [
    # Public grouped pricing (will be at /api/v1/pricing/)
    path('', PricingAPIView.as_view(), name='pricing'),
    # Builder price calculation (will be at /api/v1/pricing/builder/calculate/)
    path('calculate/', CalculatePriceView.as_view(), name='calculate-price-legacy'),
    path('builder/calculate/', CalculatePriceView.as_view(), name='calculate-price'),

    # Admin CRUD endpoints
    path('packages/admin/',
         PackageAdminViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='package-list-create'),
    path('packages/admin/<str:pk>/',
         PackageAdminViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='package-detail'),

    path('builder/admin/options/',
         BuilderOptionAdminViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='builder-option-list-create'),
    path('builder/admin/options/<int:pk>/',
         BuilderOptionAdminViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='builder-option-detail'),

    path('builder/admin/priorities/',
         BuilderPriorityAdminViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='builder-priority-list-create'),
    path('builder/admin/priorities/<int:pk>/',
         BuilderPriorityAdminViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='builder-priority-detail'),

    # Public grouped builder (via router)
    path('', include(router.urls)),
]
