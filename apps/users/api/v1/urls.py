from django.urls import path

from apps.users.api.v1.account_views import UserProfileView

from .views import (
    AdminOnlyView,
    AdminUsersListView,
    ChangeEmailView,
    ChangePasswordView,
    CustomTokenRefreshView,
    DeviceSessionsView,
    ForgotPasswordView,
    LoginHistoryView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ResendVerificationEmailView,
    ResetPasswordView,
    RestoreUserView,
    RevokeDeviceSessionView,
    SecurityEventsView,
    Setup2FAView,
    SuspendUserView,
    ToggleUserStatusView,
    UserDetailView,
    UserListView,
    Verify2FAView,
    Verify2FALoginView,
    VerifyEmailView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("", UserListView.as_view(), name="user-list"),
    path("suspend/", SuspendUserView.as_view(), name="suspend-user"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("change-email/", ChangeEmailView.as_view(), name="change-email"),
    path("login-history/", LoginHistoryView.as_view(), name="login-history"),
    path("2fa/setup/", Setup2FAView.as_view(), name="setup-2fa"),
    path("2fa/verify/", Verify2FAView.as_view(), name="verify-2fa"),
    path("2fa/login/", Verify2FALoginView.as_view(), name="2fa-login"),
    path("sessions/", DeviceSessionsView.as_view(), name="device-sessions"),
    path("sessions/revoke/", RevokeDeviceSessionView.as_view(), name="revoke-session"),
    path("security-events/", SecurityEventsView.as_view(), name="security-events"),
    path("users/<int:pk>/restore/", RestoreUserView.as_view(), name="restore-user"),
    path("admin/test/", AdminOnlyView.as_view(), name="admin-test"),
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("admin/users/", AdminUsersListView.as_view(), name="admin-users"),
    path("admin/toggle-user/", ToggleUserStatusView.as_view(), name="toggle-user-status"),
    path("admin/users/<int:pk>/", UserDetailView.as_view(), name="admin-user-detail"),
]


