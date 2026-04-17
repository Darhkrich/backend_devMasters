from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.services import upsert_client_profile

from .models import SupportTicket, TicketReply
from .serializers import (
    SupportTicketCreateSerializer,
    SupportTicketListSerializer,
    SupportTicketSerializer,
    TicketReplyCreateSerializer,
    TicketReplySerializer,
)


class TicketListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self, request):
        tickets = SupportTicket.objects.all()
        if getattr(request.user, "can_manage_staff_workspace", False):
            return tickets
        return tickets.filter(
            Q(client__email__iexact=request.user.email)
            | Q(guest_email__iexact=request.user.email)
        ).distinct()

    def get(self, request):
        tickets = self.get_queryset(request)

        ticket_status = request.query_params.get("status")
        if ticket_status:
            tickets = tickets.filter(status=ticket_status)

        priority = request.query_params.get("priority")
        if priority:
            tickets = tickets.filter(priority=priority)

        category = request.query_params.get("category")
        if category:
            tickets = tickets.filter(category=category)

        client_id = request.query_params.get("client")
        if client_id:
            tickets = tickets.filter(client_id=client_id)

        search = request.query_params.get("search")
        if search:
            tickets = tickets.filter(
                Q(subject__icontains=search)
                | Q(description__icontains=search)
                | Q(guest_email__icontains=search)
            )

        serializer = SupportTicketListSerializer(tickets, many=True)
        return Response({"count": tickets.count(), "results": serializer.data})

    def post(self, request):
        payload = request.data.copy()
        if request.user.is_authenticated:
            payload.setdefault("guest_email", request.user.email)
            payload.setdefault(
                "guest_name",
                request.user.get_full_name() or request.user.email,
            )
        if not payload.get("client") and payload.get("guest_email"):
            client = upsert_client_profile(
                name=payload.get("guest_name", ""),
                email=payload.get("guest_email", ""),
            )
            if client is not None:
                payload["client"] = client.pk

        serializer = SupportTicketCreateSerializer(data=payload)
        if serializer.is_valid():
            ticket = serializer.save()
            ticket.refresh_workflow_state()
            return Response(
                SupportTicketSerializer(ticket).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        tickets = SupportTicket.objects.all()
        if request.user.is_staff:
            return tickets
        return tickets.filter(
            Q(client__email__iexact=request.user.email)
            | Q(guest_email__iexact=request.user.email)
        ).distinct()

    def get_object(self, request, pk):
        return get_object_or_404(self.get_queryset(request), pk=pk)

    def get(self, request, pk):
        return Response(SupportTicketSerializer(self.get_object(request, pk)).data)

    def patch(self, request, pk):
        ticket = self.get_object(request, pk)
        payload = request.data
        if not getattr(request.user, "can_manage_staff_workspace", False):
            requested_status = request.data.get("status")
            if requested_status not in [SupportTicket.STATUS_RESOLVED, SupportTicket.STATUS_CLOSED]:
                return Response(
                    {"detail": "Clients can only mark their tickets as resolved or closed."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            payload = {"status": requested_status}

        serializer = SupportTicketSerializer(ticket, data=payload, partial=True)
        if serializer.is_valid():
            updated_ticket = serializer.save()
            updated_ticket.refresh_workflow_state()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not getattr(request.user, "can_manage_staff_workspace", False):
            return Response({"detail": "Only admins can delete tickets."}, status=status.HTTP_403_FORBIDDEN)

        self.get_object(request, pk).delete()
        return Response({"detail": "Ticket deleted."}, status=status.HTTP_204_NO_CONTENT)


class TicketReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def get_ticket(self, request, pk):
        tickets = SupportTicket.objects.all()
        if not getattr(request.user, "can_manage_staff_workspace", False):
            tickets = tickets.filter(
                Q(client__email__iexact=request.user.email)
                | Q(guest_email__iexact=request.user.email)
            ).distinct()
        return get_object_or_404(tickets, pk=pk)

    def post(self, request, pk):
        ticket = self.get_ticket(request, pk)
        serializer = TicketReplyCreateSerializer(data=request.data)
        if serializer.is_valid():
            reply_data = serializer.validated_data.copy()
            reply_data.pop("sender_name", None)
            reply_data.pop("sender_role", None)
            sender_role = "admin" if getattr(request.user, "can_manage_staff_workspace", False) else "client"
            sender_name = request.user.get_full_name() or request.user.email or ticket.guest_name
            reply = TicketReply.objects.create(
                ticket=ticket,
                sender_name=sender_name,
                sender_role=sender_role,
                **reply_data,
            )

            if sender_role == "admin" and ticket.status == ticket.STATUS_OPEN:
                ticket.status = ticket.STATUS_IN_PROGRESS
                update_fields = ["status", "updated_at"]
                if not ticket.first_responded_at:
                    ticket.first_responded_at = reply.created_at
                    update_fields.append("first_responded_at")
                ticket.save(update_fields=update_fields)
            elif (
                sender_role == "client"
                and ticket.status in [ticket.STATUS_RESOLVED, ticket.STATUS_CLOSED]
            ):
                ticket.status = ticket.STATUS_OPEN
                ticket.save(update_fields=["status", "updated_at"])

            ticket.refresh_workflow_state()
            return Response(TicketReplySerializer(reply).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
