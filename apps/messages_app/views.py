from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import ClientProfile
from apps.clients.services import upsert_client_profile
from apps.core.sanitization import sanitize_text
from apps.inquiries.models import Inquiry
from apps.orders.models import Order

from .models import Message, MessageThread
from .serializers import (
    MessageSerializer,
    MessageThreadListSerializer,
    MessageThreadSerializer,
    ReplySerializer,
)


class IsThreadParticipant(permissions.BasePermission):
    """Allow access only to participants of the thread (client or admin)."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, "can_manage_staff_workspace", False):
            return True
        # Check if user is linked via client, order, or inquiry
        if obj.client and obj.client.email and obj.client.email.lower() == user.email.lower():
            return True
        if obj.order and (obj.order.user == user or obj.order.client_email.lower() == user.email.lower()):
            return True
        if obj.inquiry and (obj.inquiry.user == user or obj.inquiry.email.lower() == user.email.lower()):
            return True
        return False


class ThreadListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = MessageThread.objects.select_related('client', 'order', 'inquiry')
        if getattr(self.request.user, "can_manage_staff_workspace", False):
            return qs
        return qs.filter(
            Q(client__email__iexact=self.request.user.email) |
            Q(order__user=self.request.user) |
            Q(order__client_email__iexact=self.request.user.email) |
            Q(inquiry__user=self.request.user) |
            Q(inquiry__email__iexact=self.request.user.email)
        ).distinct()

    def get(self, request):
        threads = self.get_queryset()

        # Filtering
        client_id = request.query_params.get("client")
        if client_id:
            threads = threads.filter(client_id=client_id)

        order_id = request.query_params.get("order")
        if order_id:
            threads = threads.filter(order_id=order_id)

        inquiry_id = request.query_params.get("inquiry")
        if inquiry_id:
            threads = threads.filter(inquiry_id=inquiry_id)

        archived = request.query_params.get("archived")
        if archived is not None:
            threads = threads.filter(is_archived=archived.lower() == "true")

        search = request.query_params.get("search")
        if search:
            threads = threads.filter(
                Q(subject__icontains=search) | Q(messages__body__icontains=search)
            ).distinct()

        serializer = MessageThreadListSerializer(threads, many=True, context={"request": request})
        return Response({"count": threads.count(), "results": serializer.data})

    def post(self, request):
        if request.user.is_staff and not getattr(request.user, "can_manage_staff_workspace", False):
            return Response({"detail": "Only control-center admins can create threads."}, status=status.HTTP_403_FORBIDDEN)

        subject = sanitize_text(request.data.get("subject", ""))
        body = sanitize_text(request.data.get("body", ""), multiline=True)
        if not subject or not body:
            return Response({"detail": "subject and body are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Must be linked to a client, order, or inquiry (or at least provide client_email)
        client_id = request.data.get("client")
        order_id = request.data.get("order")
        inquiry_id = request.data.get("inquiry")
        client_email = sanitize_text(request.data.get("client_email", ""))
        if not request.user.is_staff:
            client_email = request.user.email

        if not (client_id or order_id or inquiry_id or client_email):
            return Response({"detail": "Thread must be linked to a client, order, or inquiry."}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get client profile if email provided
        client = None
        if client_id:
            if request.user.is_staff:
                client = get_object_or_404(ClientProfile, pk=client_id)
            else:
                client = get_object_or_404(ClientProfile, pk=client_id, email__iexact=request.user.email)
        elif client_email:
            client = upsert_client_profile(
                name=(
                    request.user.get_full_name() or request.user.email
                    if not request.user.is_staff
                    else sanitize_text(request.data.get("client_name", ""))
                ),
                email=client_email,
                phone="" if not request.user.is_staff else sanitize_text(request.data.get("client_phone", "")),
                company="" if not request.user.is_staff else sanitize_text(request.data.get("client_company", "")),
            )

        order = None
        if order_id:
            order_queryset = Order.objects.all()
            if not request.user.is_staff:
                order_queryset = order_queryset.filter(
                    Q(user=request.user) | Q(client_email__iexact=request.user.email)
                )
            order = get_object_or_404(order_queryset, pk=order_id)

        inquiry = None
        if inquiry_id:
            inquiry_queryset = Inquiry.objects.all()
            if not request.user.is_staff:
                inquiry_queryset = inquiry_queryset.filter(
                    Q(user=request.user)
                    | Q(client__email__iexact=request.user.email)
                    | Q(email__iexact=request.user.email)
                )
            inquiry = get_object_or_404(inquiry_queryset, pk=inquiry_id)

        thread = MessageThread.objects.create(
            subject=subject,
            client=client,
            order=order,
            inquiry=inquiry,
        )

        sender_name = request.user.get_full_name() or request.user.email or getattr(client, "name", "")
        sender_role = "admin" if getattr(request.user, "can_manage_staff_workspace", False) else "client"
        Message.objects.create(
            thread=thread,
            sender_name=sender_name,
            sender_role=sender_role,
            body=body,
        )

        thread.updated_at = timezone.now()
        thread.save(update_fields=["updated_at"])

        serializer = MessageThreadSerializer(thread, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ThreadDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, request):
        queryset = MessageThread.objects.select_related('client', 'order', 'inquiry').prefetch_related(
            Prefetch('messages', queryset=Message.objects.order_by('created_at'))
        )
        if getattr(request.user, "can_manage_staff_workspace", False):
            return queryset
        return queryset.filter(
            Q(client__email__iexact=request.user.email)
            | Q(order__user=request.user)
            | Q(order__client_email__iexact=request.user.email)
            | Q(inquiry__user=request.user)
            | Q(inquiry__email__iexact=request.user.email)
        ).distinct()

    def get_object(self, request, pk):
        return get_object_or_404(self.get_queryset(request), pk=pk)

    def get(self, request, pk):
        thread = self.get_object(request, pk)

        # Mark messages as read based on viewer role
        viewer_role = "admin" if getattr(request.user, "can_manage_staff_workspace", False) else "client"
        if viewer_role == "client":
            thread.messages.filter(sender_role="admin", is_read=False).update(is_read=True)
        elif viewer_role == "admin":
            thread.messages.filter(sender_role="client", is_read=False).update(is_read=True)

        serializer = MessageThreadSerializer(thread, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        if not getattr(request.user, "can_manage_staff_workspace", False):
            return Response({"detail": "Only admins can update threads."}, status=status.HTTP_403_FORBIDDEN)

        thread = self.get_object(request, pk)
        if "subject" in request.data:
            thread.subject = sanitize_text(request.data["subject"])
        if "is_archived" in request.data:
            thread.is_archived = request.data["is_archived"]
        if request.data.get("client"):
            thread.client = get_object_or_404(ClientProfile, pk=request.data["client"])
        if request.data.get("order"):
            thread.order = get_object_or_404(Order, pk=request.data["order"])
        if request.data.get("inquiry"):
            thread.inquiry = get_object_or_404(Inquiry, pk=request.data["inquiry"])
        thread.save()

        serializer = MessageThreadSerializer(thread, context={"request": request})
        return Response(serializer.data)

    def delete(self, request, pk):
        if not getattr(request.user, "can_manage_staff_workspace", False):
            return Response({"detail": "Only admins can delete threads."}, status=status.HTTP_403_FORBIDDEN)
        thread = self.get_object(request, pk)
        thread.delete()
        return Response({"detail": "Thread deleted."}, status=status.HTTP_204_NO_CONTENT)


class ThreadReplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_thread(self, request, pk):
        qs = MessageThread.objects.select_related('client', 'order', 'inquiry')
        if not getattr(request.user, "can_manage_staff_workspace", False):
            qs = qs.filter(
                Q(client__email__iexact=request.user.email)
                | Q(order__user=request.user)
                | Q(order__client_email__iexact=request.user.email)
                | Q(inquiry__user=request.user)
                | Q(inquiry__email__iexact=request.user.email)
            ).distinct()
        return get_object_or_404(qs, pk=pk)

    def post(self, request, pk):
        thread = self.get_thread(request, pk)
        serializer = ReplySerializer(data=request.data)
        if serializer.is_valid():
            reply_data = serializer.validated_data.copy()
            reply_data.pop("sender_name", None)
            reply_data.pop("sender_role", None)
            message = Message.objects.create(
                thread=thread,
                sender_name=request.user.get_full_name() or request.user.email,
                sender_role="admin" if getattr(request.user, "can_manage_staff_workspace", False) else "client",
                **reply_data,
            )
            thread.updated_at = timezone.now()
            thread.save(update_fields=["updated_at"])
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ThreadMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        qs = MessageThread.objects.select_related('client', 'order', 'inquiry')
        if not getattr(request.user, "can_manage_staff_workspace", False):
            qs = qs.filter(
                Q(client__email__iexact=request.user.email)
                | Q(order__user=request.user)
                | Q(order__client_email__iexact=request.user.email)
                | Q(inquiry__user=request.user)
                | Q(inquiry__email__iexact=request.user.email)
            ).distinct()
        thread = get_object_or_404(qs, pk=pk)
        sender_role = "client" if getattr(request.user, "can_manage_staff_workspace", False) else "admin"
        messages = thread.messages.filter(is_read=False, sender_role=sender_role)
        updated = messages.update(is_read=True)
        return Response({"detail": f"{updated} message(s) marked as read."})
