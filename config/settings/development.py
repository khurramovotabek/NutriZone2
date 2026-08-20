"""Development settings: DEBUG on, relaxed security, browsable API, SQLite fallback."""

import sys

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

# Convenient for local frontend work against a browsable API without HTTPS.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])

# `manage.py test` shouldn't share cache state (tree cache, throttling) with
# whatever dev server/Redis instance happens to be running locally -- that
# caused real confusion once already (a stale cached category tree from a
# test run showing up in manual dev-server verification).
if "test" in sys.argv:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
