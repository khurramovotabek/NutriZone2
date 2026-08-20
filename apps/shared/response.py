"""Standard response envelope helpers.

These are available for NEW endpoints going forward (wallet, loyalty,
notifications, etc. in later phases). Existing catalog/cart/order endpoints
deliberately keep their current response shapes as-is in this phase --
the Next.js frontend is already integrated against those exact contracts,
and changing wire formats is out of scope for a foundation/structure pass.
See the Phase 1 write-up for the full rationale.
"""

from typing import Any

from rest_framework import status as http_status
from rest_framework.response import Response


def success_response(data: Any = None, message: str = "", status: int = http_status.HTTP_200_OK) -> Response:
    payload: dict[str, Any] = {"success": True, "data": data}
    if message:
        payload["message"] = message
    return Response(payload, status=status)


def error_response(
    message: str,
    code: str = "error",
    status: int = http_status.HTTP_400_BAD_REQUEST,
    errors: dict | None = None,
) -> Response:
    payload: dict[str, Any] = {"success": False, "detail": message, "code": code}
    if errors:
        payload["errors"] = errors
    return Response(payload, status=status)
