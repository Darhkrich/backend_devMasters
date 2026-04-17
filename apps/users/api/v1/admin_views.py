from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminUserCustom, ModelPermissionByMethod
from apps.security.permissions import IsAdminUserRole
from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.users.use_cases.admin import (
    delete_user,
    paginated_admin_users,
    restore_user,
    serialized_user_list,
    suspend_user,
    toggle_staff_status,
    update_user,
)

from ...throttles import SensitiveUserActionThrottle


class AdminOnlyView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        return Response({"message": "Admin access granted"})


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        return Response(serialized_user_list())


class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated, ModelPermissionByMethod]
    model = User

    def get(self, request):
        return Response({"count": User.objects.count()})

    def post(self, request):
        return Response({"message": "User creation endpoint"})


class RestoreUserView(APIView):
    permission_classes = [IsAdminUserCustom]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request, pk):
        user = get_object_or_404(User, id=pk)
        payload, status_code = restore_user(request, target_user=user)
        return Response(payload, status=status_code)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserCustom]

    def get_object(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk):
        return Response(UserSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        payload, status_code = update_user(request, target_user=user, serializer=serializer)
        return Response(payload, status=status_code)

    def delete(self, request, pk):
        payload, status_code = delete_user(self.get_object(pk))
        return Response(payload, status=status_code)


class ToggleUserStatusView(APIView):
    permission_classes = [IsAdminUserCustom]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        payload, status_code = toggle_staff_status(
            request,
            target_user=User.objects.filter(id=request.data.get("user_id")).first(),
        )
        return Response(payload, status=status_code)


class AdminUsersListView(APIView):
    permission_classes = [IsAdminUserCustom]
    throttle_classes = [SensitiveUserActionThrottle]

    def get(self, request):
        search = (request.GET.get("search") or "").strip()
        page = request.GET.get("page", 1)
        return Response(paginated_admin_users(search=search, page=page))


class SuspendUserView(APIView):
    permission_classes = [IsAdminUserCustom]
    throttle_classes = [SensitiveUserActionThrottle]

    def post(self, request):
        payload, status_code = suspend_user(
            request,
            target_user=User.objects.filter(id=request.data.get("user_id")).first(),
        )
        return Response(payload, status=status_code)
