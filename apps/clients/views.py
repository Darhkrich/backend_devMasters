from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminUserCustom

from .models import ClientProfile
from .serializers import ClientListSerializer, ClientProfileSerializer
from .services import client_has_business_records


class ClientListCreateView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        clients = ClientProfile.objects.all()

        plan = request.query_params.get("plan")
        if plan:
            clients = clients.filter(plan=plan)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            clients = clients.filter(is_active=is_active.lower() == "true")

        search = request.query_params.get("search")
        if search:
            clients = clients.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(company__icontains=search)
            )

        serializer = ClientListSerializer(clients, many=True)
        return Response({"count": clients.count(), "results": serializer.data})

    def post(self, request):
        serializer = ClientProfileSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()
            return Response(
                ClientProfileSerializer(client).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientDetailView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get_object(self, pk):
        return get_object_or_404(ClientProfile, pk=pk)

    def get(self, request, pk):
        serializer = ClientProfileSerializer(self.get_object(pk))
        return Response(serializer.data)

    def patch(self, request, pk):
        client = self.get_object(pk)
        serializer = ClientProfileSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        client = self.get_object(pk)
        if client_has_business_records(client):
            client.is_active = False
            client.save(update_fields=["is_active", "updated_at"])
            return Response(
                {
                    "detail": (
                        "Client profile deactivated because related business records exist."
                    )
                },
                status=status.HTTP_200_OK,
            )

        client.delete()
        return Response(
            {"detail": "Client profile deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )
