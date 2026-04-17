from django.urls import path
from .views import (
    ThreadListCreateView,
    ThreadDetailView,
    ThreadReplyView,
    ThreadMarkReadView,
)

urlpatterns = [
    path('threads/', ThreadListCreateView.as_view(), name='thread-list-create'),
    path('threads/<int:pk>/', ThreadDetailView.as_view(), name='thread-detail'),
    path('threads/<int:pk>/reply/', ThreadReplyView.as_view(), name='thread-reply'),
    path('threads/<int:pk>/read/', ThreadMarkReadView.as_view(), name='thread-mark-read'),
]