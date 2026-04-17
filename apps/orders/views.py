from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminUserCustom

from .models import Order
from .serializers import OrderCreateSerializer, OrderListSerializer, OrderSerializer


class OrderListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        orders = Order.objects.all()
        user = self.request.user
        if getattr(user, "can_manage_staff_workspace", False):
            return orders
        return orders.filter(Q(user=user) | Q(client_email__iexact=user.email))

    def get(self, request):
        orders = self.get_queryset()

        order_status = request.query_params.get("status")
        if order_status:
            orders = orders.filter(status=order_status)

        search = request.query_params.get("search")
        if search:
            orders = orders.filter(
                Q(reference__icontains=search)
                | Q(client_name__icontains=search)
                | Q(client_email__icontains=search)
            )

        serializer = OrderListSerializer(orders, many=True)
        return Response({"count": orders.count(), "results": serializer.data})

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdminUserCustom()]

    def get_queryset(self):
        orders = Order.objects.all()
        user = self.request.user
        if getattr(user, "can_manage_staff_workspace", False):
            return orders
        return orders.filter(Q(user=user) | Q(client_email__iexact=user.email))

    def get_object(self, pk):
        return get_object_or_404(self.get_queryset(), pk=pk)

    def get(self, request, pk):
        order = self.get_object(pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def patch(self, request, pk):
        order = self.get_object(pk)
        serializer = OrderSerializer(
            order,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        order = self.get_object(pk)
        order.delete()
        return Response({"detail": "Order deleted."}, status=status.HTTP_204_NO_CONTENT)


class OrderStatsView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        orders = Order.objects.all()
        now = timezone.now()

        total_orders = orders.count()
        monthly_revenue = (
            orders.filter(
                status__in=[Order.STATUS_IN_PROGRESS, Order.STATUS_COMPLETED],
                created_at__year=now.year,
                created_at__month=now.month,
            ).aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0.00")
        )

        active_projects = orders.filter(status=Order.STATUS_IN_PROGRESS).count()
        pending_actions = orders.filter(
            status__in=[
                Order.STATUS_PENDING,
                Order.STATUS_REVIEWED,
                Order.STATUS_AWAITING_CLIENT,
            ]
        ).count()

        status_counts = {
            status_value: orders.filter(status=status_value).count()
            for status_value, _ in Order.STATUS_CHOICES
        }

        return Response(
            {
                "total_orders": total_orders,
                "monthly_revenue": float(monthly_revenue),
                "active_projects": active_projects,
                "pending_actions": pending_actions,
                "status_breakdown": status_counts,
            }
        )
