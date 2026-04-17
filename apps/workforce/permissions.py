from rest_framework.permissions import BasePermission


def can_manage_staff_workspace(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, "can_manage_staff_workspace", False)
    )


class IsStaffWorkspaceUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class CanManageStaffWorkspace(BasePermission):
    def has_permission(self, request, view):
        return can_manage_staff_workspace(request.user)
