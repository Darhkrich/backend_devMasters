from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppServiceViewSet, AppServiceAdminViewSet

public_router = DefaultRouter()
public_router.register(r'', AppServiceViewSet, basename='appservice')

urlpatterns = [
    # Admin CRUD endpoints – these must come before the router's wildcard patterns
    path('admin/', AppServiceAdminViewSet.as_view({'get': 'list', 'post': 'create'}), name='appservice-admin-list'),
    path('admin/<str:pk>/', AppServiceAdminViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='appservice-admin-detail'),
    # Public router (handles '' and '<pk>/')
    path('', include(public_router.urls)),
]