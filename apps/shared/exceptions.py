from rest_framework.views import exception_handler as drf_exception_handler


class ServiceError(Exception):
    """Raised by service-layer functions for expected business rule violations.

    Views catch this and translate it into a clean 400 response, keeping
    business logic in services.py free of any HTTP/DRF concerns.
    """

    def __init__(self, message, code="error"):
        self.message = message
        self.code = code
        super().__init__(message)


def custom_exception_handler(exc, context):
    """Wrap DRF's default handler to produce a consistent error envelope.

    Response shape: {"detail": "...", "code": "..."}
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        detail = response.data
        if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
            response.data = {"detail": detail["detail"], "code": getattr(exc, "default_code", "error")}
        else:
            response.data = {"detail": detail, "code": getattr(exc, "default_code", "error")}
    return response
