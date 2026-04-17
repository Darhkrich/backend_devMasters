from django.core.paginator import Paginator
from rest_framework import status

from apps.security.utils import log_security_event
from apps.users.models import User
from apps.users.serializers import UserSerializer


def restore_user(request, *, target_user):
    if target_user.is_superuser:
        return {"error": "Superusers cannot be modified"}, status.HTTP_403_FORBIDDEN

    target_user.is_active = True
    target_user.save(update_fields=["is_active"])
    log_security_event(
        user=request.user,
        event_type="ADMIN_ACCESS",
        request=request,
        metadata={"action": "restore_user", "target_user_id": target_user.id},
    )
    return {"status": "restored", "is_active": target_user.is_active}, status.HTTP_200_OK


def update_user(request, *, target_user, serializer):
    if "is_active" in request.data and request.data["is_active"] is False:
        if target_user.is_superuser:
            return {"error": "Superusers cannot be suspended"}, status.HTTP_403_FORBIDDEN
        if target_user == request.user:
            return {"error": "You cannot suspend your own account"}, status.HTTP_403_FORBIDDEN

    serializer.is_valid(raise_exception=True)
    serializer.save()
    return serializer.data, status.HTTP_200_OK


def delete_user(target_user):
    if target_user.is_superuser:
        return {"error": "Superusers cannot be deleted"}, status.HTTP_403_FORBIDDEN

    target_user.delete()
    return {"message": "User deleted"}, status.HTTP_200_OK


def toggle_staff_status(request, *, target_user):
    if not target_user:
        return {"error": "User not found"}, status.HTTP_404_NOT_FOUND
    if target_user.is_superuser:
        return {"error": "Superusers cannot be modified"}, status.HTTP_403_FORBIDDEN

    target_user.is_staff = not target_user.is_staff
    target_user.save(update_fields=["is_staff"])
    log_security_event(
        user=request.user,
        event_type="ADMIN_ACCESS",
        request=request,
        metadata={"action": "toggle_staff", "target_user_id": target_user.id},
    )
    return {"status": "success", "is_staff": target_user.is_staff}, status.HTTP_200_OK


def suspend_user(request, *, target_user):
    if not target_user:
        return {"error": "User not found"}, status.HTTP_404_NOT_FOUND
    if target_user.is_superuser:
        return {"error": "Superusers cannot be suspended"}, status.HTTP_403_FORBIDDEN

    target_user.is_active = False
    target_user.save(update_fields=["is_active"])
    log_security_event(
        user=request.user,
        event_type="ADMIN_ACCESS",
        request=request,
        metadata={"action": "suspend_user", "target_user_id": target_user.id},
    )
    return {"status": "suspended"}, status.HTTP_200_OK


def paginated_admin_users(*, search, page):
    users = User.objects.all().order_by("-date_joined")
    if search:
        users = users.filter(email__icontains=search)

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(page)
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined,
            }
            for user in page_obj
        ],
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
    }


def serialized_user_list():
    users = User.objects.all().order_by("-date_joined")
    return UserSerializer(users, many=True).data
