from django.urls import path

from .views import (
    AdminSecurityDashboardView,
    BlockedIPsView,
    LoginTrendView,
    ResolveAlertView,
    SecurityAlertsView,
    SuspiciousLoginView,
    TopAttackingIPsView,
    UnblockIPView,
    UnlockUserView,
)


urlpatterns = [
    path("dashboard/", AdminSecurityDashboardView.as_view()),
    path("suspicious-logins/", SuspiciousLoginView.as_view()),
    path("unlock-user/", UnlockUserView.as_view()),
    path("top-attacking-ips/", TopAttackingIPsView.as_view()),
    path("blocked-ips/", BlockedIPsView.as_view()),
    path("unblock-ip/", UnblockIPView.as_view()),
    path("login-trend/", LoginTrendView.as_view()),
    path("alerts/", SecurityAlertsView.as_view()),
    path("resolve-alert/", ResolveAlertView.as_view()),
    path("resolve-arlert/", ResolveAlertView.as_view()),
]
