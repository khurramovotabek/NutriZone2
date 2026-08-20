from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.exceptions import ServiceError

from ..models import CartItem
from ..selectors import cart_with_items
from ..services import CartService
from .serializers import AddCartItemSerializer, CartSerializer, UpdateCartItemSerializer

CART_HEADER = "HTTP_X_CART_ID"


class CartBaseView(APIView):
    """Base view resolving the caller's cart from auth or the X-Cart-Id header."""

    permission_classes = [permissions.AllowAny]

    def get_cart(self, request):
        cart_id = request.META.get(CART_HEADER)
        user = request.user if request.user.is_authenticated else None
        return CartService.get_or_create_cart(user=user, cart_id=cart_id)

    def cart_response(self, cart, status_code=status.HTTP_200_OK):
        # Re-fetch through the prefetching selector at RESPONSE time (after
        # any mutation this request performed) so serializing items
        # (variant -> product -> images/translations) doesn't N+1 -- and,
        # critically, doesn't serialize a stale prefetch cache from before
        # the mutation. Fetching this in get_cart() instead was a real bug:
        # a cart fetched (and its `.items` prefetched) BEFORE an add-to-cart
        # write still shows the old, empty items list, since prefetch_related
        # caches in Python and a later write via a different queryset
        # doesn't invalidate that cache.
        cart = cart_with_items(cart.id).first() or cart
        data = CartSerializer(cart, context={"request": self.request}).data
        response = Response(data, status=status_code)
        response["X-Cart-Id"] = str(cart.id)
        return response


class CartDetailView(CartBaseView):
    def get(self, request):
        cart = self.get_cart(request)
        return self.cart_response(cart)

    def delete(self, request):
        cart = self.get_cart(request)
        CartService.clear(cart)
        return self.cart_response(cart)


class CartItemListView(CartBaseView):
    def post(self, request):
        cart = self.get_cart(request)
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            CartService.add_item(
                cart, serializer.validated_data["variant"], serializer.validated_data["quantity"]
            )
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)
        return self.cart_response(cart, status.HTTP_201_CREATED)


class CartItemDetailView(CartBaseView):
    def _get_item(self, cart, item_id):
        return get_object_or_404(CartItem, pk=item_id, cart=cart)

    def patch(self, request, item_id):
        cart = self.get_cart(request)
        item = self._get_item(cart, item_id)
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            CartService.set_quantity(cart, item, serializer.validated_data["quantity"])
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)
        return self.cart_response(cart)

    def delete(self, request, item_id):
        cart = self.get_cart(request)
        item = self._get_item(cart, item_id)
        CartService.remove_item(cart, item)
        return self.cart_response(cart)


class CartItemIncreaseView(CartBaseView):
    def post(self, request, item_id):
        cart = self.get_cart(request)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        try:
            CartService.increase_quantity(cart, item)
        except ServiceError as exc:
            return Response({"detail": exc.message, "code": exc.code}, status=status.HTTP_400_BAD_REQUEST)
        return self.cart_response(cart)


class CartItemDecreaseView(CartBaseView):
    def post(self, request, item_id):
        cart = self.get_cart(request)
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        CartService.decrease_quantity(cart, item)
        return self.cart_response(cart)
