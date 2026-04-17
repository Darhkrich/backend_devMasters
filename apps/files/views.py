from pathlib import PurePosixPath

from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from django.utils.text import get_valid_filename
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ProjectFile
from .serializers import (
    ProjectFileAdminUpdateSerializer,
    ProjectFileClientUpdateSerializer,
    ProjectFileCreateSerializer,
    ProjectFileSerializer,
)


class ProjectFileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ProjectFile.objects.select_related(
            "order",
            "inquiry",
            "uploader",
            "reviewed_by",
        )
        user = self.request.user

        if not getattr(user, "can_manage_staff_workspace", False):
            queryset = queryset.filter(
                Q(order__user=user)
                | Q(order__client_email__iexact=user.email)
                | Q(inquiry__user=user)
                | Q(inquiry__email__iexact=user.email)
            ).distinct()

        order_id = self.request.query_params.get("order")
        if order_id:
            queryset = queryset.filter(order_id=order_id)

        inquiry_id = self.request.query_params.get("inquiry")
        if inquiry_id:
            queryset = queryset.filter(inquiry_id=inquiry_id)

        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(uploader_role=role)

        review_status = self.request.query_params.get("status")
        if review_status:
            queryset = queryset.filter(review_status=review_status)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectFileCreateSerializer
        if self.action in {"update", "partial_update"}:
            if getattr(self.request.user, "can_manage_staff_workspace", False):
                return ProjectFileAdminUpdateSerializer
            return ProjectFileClientUpdateSerializer
        return ProjectFileSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        project_file = serializer.save(
            uploader=request.user,
            uploader_role="admin" if getattr(request.user, "can_manage_staff_workspace", False) else "client",
        )
        output = ProjectFileSerializer(project_file, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ProjectFileSerializer(
            queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        return Response({"count": queryset.count(), "results": serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output = ProjectFileSerializer(serializer.instance, context=self.get_serializer_context())
        return Response(output.data)

    def perform_update(self, serializer):
        update_kwargs = {}
        if getattr(self.request.user, "can_manage_staff_workspace", False) and {
            "review_status",
            "review_notes",
        } & set(serializer.validated_data.keys()):
            update_kwargs["reviewed_by"] = self.request.user
            update_kwargs["reviewed_at"] = timezone.now()
        serializer.save(**update_kwargs)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        file_obj = self.get_object()
        if not file_obj.file:
            return Response(
                {"detail": "No uploaded file is attached to this record."},
                status=status.HTTP_404_NOT_FOUND,
            )

        safe_name = get_valid_filename(
            file_obj.file_name or PurePosixPath(file_obj.file.name).name or "download"
        )
        file_obj.file.open("rb")
        return FileResponse(file_obj.file, as_attachment=True, filename=safe_name)

    def destroy(self, request, *args, **kwargs):
        file_obj = self.get_object()
        if file_obj.file:
            file_obj.file.delete(save=False)
        return super().destroy(request, *args, **kwargs)
