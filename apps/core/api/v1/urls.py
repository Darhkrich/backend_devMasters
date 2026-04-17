from django.urls import path

from .views import APIVersionsView, LivenessView, MetricsView, ReadinessView


urlpatterns = [
    path("health/live/", LivenessView.as_view(), name="api-live"),
    path("health/ready/", ReadinessView.as_view(), name="api-ready"),
    path("versions/", APIVersionsView.as_view(), name="api-versions"),
    path("metrics/", MetricsView.as_view(), name="api-metrics"),
]
