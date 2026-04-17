from rest_framework.permissions import BasePermission


def _has_role(user, *allowed_roles):
    role = (getattr(user, "role", "") or "").upper()
    return role in {item.upper() for item in allowed_roles}


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(
            user.is_superuser
            or getattr(user, "can_manage_staff_workspace", False)
            or _has_role(user, "ADMIN")
        )


class IsModeratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(
            user.is_superuser
            or getattr(user, "can_manage_staff_workspace", False)
            or _has_role(user, "ADMIN", "MODERATOR")
        )


class IsSecurityAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(
            user.is_superuser
            or getattr(user, "can_manage_staff_workspace", False)
            or _has_role(user, "ADMIN", "MODERATOR")
        )
