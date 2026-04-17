
# automation/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AutomationViewSet, BundleViewSet, AutomationAdminViewSet, BundleAdminViewSet

router = DefaultRouter()
router.register(r'automations', AutomationViewSet, basename='automation')
router.register(r'bundles', BundleViewSet, basename='bundle')
router.register(r'admin/automations', AutomationAdminViewSet, basename='automation-admin')
router.register(r'admin/bundles', BundleAdminViewSet, basename='bundle-admin')

urlpatterns = [
    path('', include(router.urls)),
]