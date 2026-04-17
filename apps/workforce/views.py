from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StaffTask, StaffTaskActivity
from .permissions import IsStaffWorkspaceUser, can_manage_staff_workspace
from .serializers import StaffTaskSerializer, TeamMemberSerializer


User = get_user_model()


def _log_task_activity(task, *, actor, event_type, message, metadata=None):
    StaffTaskActivity.objects.create(
        task=task,
        actor=actor,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


def _team_snapshot():
    queryset = (
        User.objects.filter(is_staff=True, is_active=True)
        .exclude(staff_team="")
        .values("staff_team")
        .annotate(member_count=Count("id"))
        .order_by("staff_team")
    )
    return list(queryset)


class WorkforceDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStaffWorkspaceUser]

    def get(self, request):
        now = timezone.now()
        this_week = now - timedelta(days=7)
        task_queryset = StaffTask.objects.filter(is_deleted=False)

        if can_manage_staff_workspace(request.user):
            payload = {
                "workspace_mode": "control_center",
                "workspace_name": request.user.workspace_name,
                "staff_count": User.objects.filter(is_staff=True, is_active=True).count(),
                "open_tasks": task_queryset.exclude(status=StaffTask.STATUS_DONE).count(),
                "in_review_tasks": task_queryset.filter(status=StaffTask.STATUS_IN_REVIEW).count(),
                "overdue_tasks": task_queryset.filter(
                    due_at__lt=now,
                    is_deleted=False,
                ).exclude(status=StaffTask.STATUS_DONE).count(),
                "unassigned_tasks": task_queryset.filter(assigned_to__isnull=True).count(),
                "completed_this_week": task_queryset.filter(
                    completed_at__gte=this_week,
                    status=StaffTask.STATUS_DONE,
                ).count(),
                "team_snapshot": _team_snapshot(),
                "focus_tasks": StaffTaskSerializer(
                    task_queryset.select_related("assigned_to", "assigned_by", "order", "inquiry", "support_ticket")[:6],
                    many=True,
                ).data,
            }
            return Response(payload)

        personal_queryset = task_queryset.filter(assigned_to=request.user)
        payload = {
            "workspace_mode": "staff_workspace",
            "workspace_name": request.user.workspace_name,
            "staff_team": request.user.staff_team,
            "staff_title": request.user.staff_title,
            "assigned_tasks": personal_queryset.count(),
            "todo_tasks": personal_queryset.filter(status=StaffTask.STATUS_TODO).count(),
            "in_progress_tasks": personal_queryset.filter(status=StaffTask.STATUS_IN_PROGRESS).count(),
            "review_tasks": personal_queryset.filter(status=StaffTask.STATUS_IN_REVIEW).count(),
            "blocked_tasks": personal_queryset.filter(status=StaffTask.STATUS_BLOCKED).count(),
            "overdue_tasks": personal_queryset.filter(due_at__lt=now).exclude(status=StaffTask.STATUS_DONE).count(),
            "completed_this_week": personal_queryset.filter(
                completed_at__gte=this_week,
                status=StaffTask.STATUS_DONE,
            ).count(),
            "focus_tasks": StaffTaskSerializer(
                personal_queryset.select_related("assigned_to", "assigned_by", "order", "inquiry", "support_ticket")[:6],
                many=True,
            ).data,
        }
        return Response(payload)


class TeamMemberListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffWorkspaceUser]

    def get_queryset(self, request):
        queryset = User.objects.all().order_by("first_name", "last_name", "email")
        include_non_staff = request.GET.get("include_non_staff") == "true"
        search = (request.GET.get("search") or "").strip()

        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(staff_title__icontains=search)
            )

        if not can_manage_staff_workspace(request.user) or not include_non_staff:
            queryset = queryset.filter(is_staff=True)

        return queryset.annotate(
            active_task_count=Count(
                "assigned_staff_tasks",
                filter=Q(
                    assigned_staff_tasks__is_deleted=False,
                    assigned_staff_tasks__status__in=[
                        StaffTask.STATUS_TODO,
                        StaffTask.STATUS_IN_PROGRESS,
                        StaffTask.STATUS_IN_REVIEW,
                        StaffTask.STATUS_BLOCKED,
                    ],
                ),
                distinct=True,
            ),
            overdue_task_count=Count(
                "assigned_staff_tasks",
                filter=Q(
                    assigned_staff_tasks__is_deleted=False,
                    assigned_staff_tasks__due_at__lt=timezone.now(),
                )
                & ~Q(assigned_staff_tasks__status=StaffTask.STATUS_DONE),
                distinct=True,
            ),
        )

    def get(self, request):
        serializer = TeamMemberSerializer(
            self.get_queryset(request),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class TeamMemberDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStaffWorkspaceUser]

    def patch(self, request, pk):
        if not can_manage_staff_workspace(request.user):
            return Response({"detail": "Only admins can update staff records."}, status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, pk=pk)
        serializer = TeamMemberSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StaffTaskListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffWorkspaceUser]

    def get_queryset(self, request):
        queryset = (
            StaffTask.objects.filter(is_deleted=False)
            .select_related("assigned_to", "assigned_by", "order", "inquiry", "support_ticket")
            .prefetch_related("activities")
            .order_by("due_at", "-created_at")
        )
        search = (request.GET.get("search") or "").strip()
        status_filter = (request.GET.get("status") or "").strip()
        team = (request.GET.get("team") or "").strip()
        priority = (request.GET.get("priority") or "").strip()
        assigned_to = request.GET.get("assigned_to")
        mine = request.GET.get("mine") == "true"

        if not can_manage_staff_workspace(request.user):
            queryset = queryset.filter(assigned_to=request.user)
        elif mine:
            queryset = queryset.filter(assigned_to=request.user)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(assigned_to__first_name__icontains=search)
                | Q(assigned_to__last_name__icontains=search)
                | Q(assigned_to__email__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if team:
            queryset = queryset.filter(team=team)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assigned_to and can_manage_staff_workspace(request.user):
            queryset = queryset.filter(assigned_to_id=assigned_to)

        return queryset

    def get(self, request):
        serializer = StaffTaskSerializer(
            self.get_queryset(request),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        if not can_manage_staff_workspace(request.user):
            return Response({"detail": "Only admins can assign staff tasks."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StaffTaskSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save(assigned_by=request.user)

        _log_task_activity(
            task,
            actor=request.user,
            event_type=StaffTaskActivity.EVENT_CREATED,
            message=f"Task created by {request.user.email}.",
        )
        if task.assigned_to:
            _log_task_activity(
                task,
                actor=request.user,
                event_type=StaffTaskActivity.EVENT_ASSIGNED,
                message=f"Task assigned to {task.assigned_to.email}.",
                metadata={"assigned_to_id": task.assigned_to_id},
            )

        return Response(
            StaffTaskSerializer(task, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class StaffTaskDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStaffWorkspaceUser]

    def get_object(self, request, pk):
        queryset = StaffTask.objects.filter(is_deleted=False).select_related(
            "assigned_to",
            "assigned_by",
            "order",
            "inquiry",
            "support_ticket",
        ).prefetch_related("activities")
        task = get_object_or_404(queryset, pk=pk)
        if can_manage_staff_workspace(request.user) or task.assigned_to_id == request.user.id:
            return task
        return get_object_or_404(StaffTask.objects.none(), pk=pk)

    def get(self, request, pk):
        task = self.get_object(request, pk)
        return Response(StaffTaskSerializer(task, context={"request": request}).data)

    def patch(self, request, pk):
        task = self.get_object(request, pk)
        before = {
            "assigned_to_id": task.assigned_to_id,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "staff_notes": task.staff_notes,
            "admin_notes": task.admin_notes,
        }

        if can_manage_staff_workspace(request.user):
            payload = request.data
        else:
            payload = {
                key: value
                for key, value in request.data.items()
                if key in {"status", "progress_percent", "staff_notes"}
            }
            if not payload:
                return Response(
                    {"detail": "You can only update your status, progress, or staff notes."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = StaffTaskSerializer(
            task,
            data=payload,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        updated_task = serializer.save()

        after = {
            "assigned_to_id": updated_task.assigned_to_id,
            "status": updated_task.status,
            "progress_percent": updated_task.progress_percent,
            "staff_notes": updated_task.staff_notes,
            "admin_notes": updated_task.admin_notes,
        }

        if before["assigned_to_id"] != after["assigned_to_id"] and updated_task.assigned_to:
            _log_task_activity(
                updated_task,
                actor=request.user,
                event_type=StaffTaskActivity.EVENT_ASSIGNED,
                message=f"Task assigned to {updated_task.assigned_to.email}.",
                metadata={"assigned_to_id": updated_task.assigned_to_id},
            )
        if before["status"] != after["status"]:
            _log_task_activity(
                updated_task,
                actor=request.user,
                event_type=StaffTaskActivity.EVENT_STATUS,
                message=f"Status changed to {updated_task.status}.",
            )
        if before["progress_percent"] != after["progress_percent"]:
            _log_task_activity(
                updated_task,
                actor=request.user,
                event_type=StaffTaskActivity.EVENT_PROGRESS,
                message=f"Progress updated to {updated_task.progress_percent}%.",
            )
        if before["staff_notes"] != after["staff_notes"] or before["admin_notes"] != after["admin_notes"]:
            _log_task_activity(
                updated_task,
                actor=request.user,
                event_type=StaffTaskActivity.EVENT_NOTE,
                message="Task notes updated.",
            )
        if before == after:
            _log_task_activity(
                updated_task,
                actor=request.user,
                event_type=StaffTaskActivity.EVENT_UPDATED,
                message="Task details updated.",
            )

        return Response(StaffTaskSerializer(updated_task, context={"request": request}).data)

    def delete(self, request, pk):
        if not can_manage_staff_workspace(request.user):
            return Response({"detail": "Only admins can delete staff tasks."}, status=status.HTTP_403_FORBIDDEN)

        task = self.get_object(request, pk)
        task.is_deleted = True
        task.save(update_fields=["is_deleted", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
