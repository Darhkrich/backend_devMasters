from django.urls import path
from .views import TicketListCreateView, TicketDetailView, TicketReplyView

urlpatterns = [
    path('tickets/', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:pk>/reply/', TicketReplyView.as_view(), name='ticket-reply'),
]
