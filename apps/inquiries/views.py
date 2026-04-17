from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminUserCustom
from apps.orders.serializers import OrderSerializer
from apps.services.convert_inquiry_to_order import convert_inquiry_to_order

from .models import Inquiry
from .serializers import InquiryCreateSerializer, InquiryListSerializer, InquirySerializer


class InquiryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        inquiries = Inquiry.objects.all()
        user = self.request.user
        if getattr(user, "can_manage_staff_workspace", False):
            return inquiries
        return inquiries.filter(
            Q(user=user) | Q(client__email__iexact=user.email) | Q(email__iexact=user.email)
        )

    def get(self, request):
        inquiries = self.get_queryset()

        status_filter = request.query_params.get("status")
        if status_filter:
            inquiries = inquiries.filter(status=status_filter)

        search = request.query_params.get("search")
        if search:
            inquiries = inquiries.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(company__icontains=search)
                | Q(subject__icontains=search)
            )

        serializer = InquiryListSerializer(inquiries, many=True)
        return Response({"count": inquiries.count(), "results": serializer.data})

    def post(self, request):
        serializer = InquiryCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            inquiry = serializer.save()
            return Response(
                InquirySerializer(inquiry).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InquiryDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdminUserCustom()]

    def get_queryset(self):
        inquiries = Inquiry.objects.all()
        user = self.request.user
        if getattr(user, "can_manage_staff_workspace", False):
            return inquiries
        return inquiries.filter(
            Q(user=user) | Q(client__email__iexact=user.email) | Q(email__iexact=user.email)
        )

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get(self, request, pk):
        inquiry = self.get_object(pk)
        serializer = InquirySerializer(inquiry)
        return Response(serializer.data)

    def patch(self, request, pk):
        inquiry = self.get_object(pk)
        serializer = InquirySerializer(
            inquiry,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        inquiry = self.get_object(pk)
        inquiry.delete()
        return Response({"detail": "Inquiry deleted."}, status=status.HTTP_204_NO_CONTENT)


class InquiryConvertToOrderView(APIView):
    permission_classes = [IsAdminUserCustom]

    def post(self, request, pk):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        order, created = convert_inquiry_to_order(
            inquiry=inquiry,
            actor=request.user,
            admin_notes=request.data.get("admin_notes", ""),
            initial_message=request.data.get("initial_message", ""),
        )
        payload = OrderSerializer(order).data
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(payload, status=response_status)
