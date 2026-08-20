"""Cross-cutting constants shared by multiple domains.

Domain-specific choices (order status, variant status, etc.) stay in their
own app's models.py -- this file is only for values genuinely shared by two
or more apps, to avoid becoming a dumping ground.
"""

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

DEFAULT_CURRENCY = "UZS"

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
# Adding a language later is just adding a new tuple here + inserting
# translation rows -- no schema migration needed on any translated model.
LANGUAGES = [
    ("uz", "Uzbek"),
    ("ru", "Russian"),
    ("en", "English"),
]
LANGUAGE_CODES = [code for code, _ in LANGUAGES]
DEFAULT_LANGUAGE = "uz"
# Requested language missing -> try English -> fall back to the default.
LANGUAGE_FALLBACK_CHAIN = ["en", DEFAULT_LANGUAGE]

# Shared cache timeouts (seconds), used by apps.shared.cache helpers and by
# individual apps' selectors when caching read-heavy querysets.
CACHE_TTL_SHORT = 60
CACHE_TTL_MEDIUM = 5 * 60
CACHE_TTL_LONG = 60 * 60

# Header the frontend uses to carry a guest cart identifier.
CART_ID_HEADER = "X-Cart-Id"
