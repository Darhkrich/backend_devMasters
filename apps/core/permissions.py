from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission




class IsAdminUserCustom(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "can_manage_staff_workspace", False)
        )


class PublicPostAndAdminOtherwise(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return True

        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "can_manage_staff_workspace", False)
        )


class HasUserViewPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.has_perm("users.view_user"))


class InternalMetricsPermission(BasePermission):
    def has_permission(self, request, view):
        configured_token = getattr(settings, "METRICS_AUTH_TOKEN", "")
        provided_token = request.headers.get("X-Metrics-Key", "")
        if configured_token and provided_token:
            if constant_time_compare(provided_token, configured_token):
                return True
            raise PermissionDenied("Invalid metrics token.")
        if configured_token:
            raise NotAuthenticated("Metrics token required.")

        user = request.user
        if not user or not user.is_authenticated:
            raise NotAuthenticated("Authentication required.")
        return bool(getattr(user, "can_manage_staff_workspace", False))





class ModelPermissionByMethod(BasePermission):
    permission_map = {
        "GET": "view",
        "HEAD": "view",
        "OPTIONS": "view",
        "POST": "add",
        "PUT": "change",
        "PATCH": "change",
        "DELETE": "delete",
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        model = getattr(view, "model", None)
        if model is None:
            return False

        action = self.permission_map.get(request.method)
        if not action:
            return False

        app_label = model._meta.app_label
        model_name = model._meta.model_name

        permission = f"{app_label}.{action}_{model_name}"

        user = request.user

        return bool(user and user.has_perm(permission))
    





class IsSelfOrHasModelPermission(BasePermission):
    permission_map = {
        "PATCH": "change",
        "PUT": "change",
        "DELETE": "delete",
    }

    def has_object_permission(self, request, view, obj):
        # If user is modifying their own record
        if hasattr(obj, 'user') and obj.user == request.user:
            return True

        # Otherwise check model permission
        action = self.permission_map.get(request.method)
        if not action:
            return False

        app_label = obj._meta.app_label
        model_name = obj._meta.model_name

        permission = f"{app_label}.{action}_{model_name}"

        user = request.user
        return bool(user and user.has_perm(permission))
