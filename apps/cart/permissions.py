"""Permission classes for the cart domain.

Carts are deliberately open (AllowAny) since guest checkout must work
without an account -- see apps.cart.api.views.CartBaseView.
"""
