from django.urls import path, include


urlpatterns = [
    path("v1/auth/", include("apps.users.api.v1.urls")),
    path("v1/security/", include("apps.security.api.v1.urls")),
    path("v1/audit/", include("apps.audit.api.v1.urls")),
    path("v1/services/", include("apps.services.urls")),
    path("v1/pricing/", include("apps.pricing.urls")),
    path("v1/templates/", include("apps.templates.urls")),
    path("v1/ai-services/", include("apps.ai_services.urls")),
    path("v1/clients/", include("apps.clients.urls")),
    path("v1/inquiries/", include("apps.inquiries.urls")),
    path("v1/orders/", include("apps.orders.urls")),
    path("v1/messages/", include("apps.messages_app.urls")),
    path("v1/files/", include("apps.files.urls")),
    path("v1/support/", include("apps.support.urls")),
]
