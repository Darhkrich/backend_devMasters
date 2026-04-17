from django.urls import re_path
from .consumers import SecurityEventsConsumer

websocket_urlpatterns = [
    re_path(r"ws/security/$", SecurityEventsConsumer.as_asgi()),
]