from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenVerifyView

from apps.users.api.v1.views import CustomTokenObtainPairView, CustomTokenRefreshView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.api.v1.urls")),
    path("api/v1/users/", include("apps.users.api.v1.urls")),
    path("api/v1/core/", include("apps.core.api.v1.urls")),
    path("api/v1/security/", include("apps.security.api.v1.urls")),
    path("api/v1/audit/", include("apps.audit.api.v1.urls")),
    path("api/v1/services/", include("apps.services.urls")),
    path("api/v1/pricing/", include("apps.pricing.urls")),
    path("api/v1/templates/", include("apps.templates.urls")),
    path("api/v1/automation/", include("apps.automation.urls")),
    path("api/v1/clients/", include("apps.clients.urls")),
    path("api/v1/inquiries/", include("apps.inquiries.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/workforce/", include("apps.workforce.urls")),
    path("api/v1/messages/", include("apps.messages_app.urls")),
    path("api/v1/files/", include("apps.files.urls")),
    path("api/v1/support/", include("apps.support.urls")),
    path("api/v1/auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh_root"),
    path("api/v1/auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
     path("api/v1/notifications/", include("apps.notifications.urls")),  # or "apps.notifications.urls"

]

if settings.DEBUG or getattr(settings, 'FORCE_SERVE_MEDIA', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


