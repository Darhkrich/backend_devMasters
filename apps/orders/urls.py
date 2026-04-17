from django.urls import path
from .views import OrderListCreateView, OrderDetailView, OrderStatsView

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),
]