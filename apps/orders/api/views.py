from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.cart.api.views import CART_HEADER
from apps.cart.services import CartService
from apps.shared.exceptions import ServiceError
from apps.shared.i18n import resolve_language
from apps.shared.pagination import StandardResultsPagination
from apps.shared.permissions import IsAdminUser

from ..models import Order
from ..selectors import orders_visible_to_user
from ..services import OrderService
from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer,
)


class OrderViewSet(viewsets.GenericViewSet):
    """Checkout + order management.

    - create: public (guest or authenticated) -- turns the caller's current
      cart into an order.
    - list/retrieve: authenticated users see only their own orders; admins
      see everything.
    - set_status: admin-only workflow action (NEW -> PENDING -> ACCEPTED,
      or -> CANCELLED).
    """

    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        if self.action == "set_status":
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "set_status":
            return OrderStatusUpdateSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        return orders_visible_to_user(self.request.user)

    def create(self, request):
        cart_id = request.META.get(CART_HEADER)
        user = request.user if request.user.is_authenticated else None
        cart = CartService.get_or_create_cart(user=user, cart_id=cart_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.create_from_cart(
                cart, serializer.validated_data, user=user, language=resolve_language(request)
            )
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        order = get_object_or_404(self.get_queryset(), pk=pk)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["patch"], url_path="status")
    def set_status(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = OrderService.change_status(order, serializer.validated_data["status"])
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderDetailSerializer(order).data)
