"""Production settings: DEBUG off, strict security, requires real infra via env vars."""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

if SECRET_KEY == "django-insecure-change-me-in-production":  # noqa: F405
    raise RuntimeError("SECRET_KEY must be set via environment in production.")

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 7)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# The browsable API's HTML renderer is a dev convenience; keep production
# responses JSON-only.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]  # noqa: F405
