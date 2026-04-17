from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Anyone can read
        if request.method in SAFE_METHODS:
            return True

        # Only admin can create/update/delete
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "can_manage_staff_workspace", False)
        )
    
