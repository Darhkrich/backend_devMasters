from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.public import PublicTemplateViewSet
from .views.admin import AdminTemplateViewSet

router = DefaultRouter()
router.register("public", PublicTemplateViewSet, basename="public-templates")
router.register("admin", AdminTemplateViewSet, basename="admin-templates")

urlpatterns = [
    path("", include(router.urls)),
]
