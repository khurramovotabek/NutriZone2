"""Shared internationalization helpers.

Every translatable model (Category, Brand, Product, ...) follows the same
shape: a `translations` related manager holding one row per language, each
row having a `language` field. These functions are the ONLY place fallback
logic lives -- serializers call get_translation() and never reimplement
the requested->en->uz chain themselves.
"""

from dataclasses import dataclass
from typing import Any

from django.http import HttpRequest

from .constants import DEFAULT_LANGUAGE, LANGUAGE_CODES, LANGUAGE_FALLBACK_CHAIN


def resolve_language(request: HttpRequest | None) -> str:
    """Resolve the active language for this request.

    Priority: explicit `?lang=` query param, then `Accept-Language` header,
    then the default. Deliberately query-param-first (not header-first) --
    it's explicit, cacheable, and trivial to test, whereas Accept-Language
    parsing is a fallback convenience for clients that don't set `lang`.
    """
    if request is None:
        return DEFAULT_LANGUAGE

    requested = request.query_params.get("lang") if hasattr(request, "query_params") else None
    if not requested:
        requested = request.GET.get("lang")
    if requested and requested in LANGUAGE_CODES:
        return requested

    accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for part in accept_language.split(","):
        code = part.split(";")[0].strip().split("-")[0].lower()
        if code in LANGUAGE_CODES:
            return code

    return DEFAULT_LANGUAGE


def pick_translation(translations: list, language: str):
    """Pick the best-matching translation from an already-fetched list
    (never queries the DB -- callers must prefetch_related("translations")).

    Returns (translation_or_None, language_actually_used).
    """
    by_language = {t.language: t for t in translations}

    for candidate in [language, *LANGUAGE_FALLBACK_CHAIN]:
        if candidate in by_language:
            return by_language[candidate], candidate

    if translations:
        first = translations[0]
        return first, first.language

    return None, language


@dataclass
class ResolvedTranslation:
    """Result of resolving a translatable object's content for a given
    requested language. `translation` is the picked row (or None if the
    object has no translations at all yet -- e.g. a brand-new product an
    admin hasn't filled in translations for). `translation_available`
    is False whenever a fallback occurred, so callers can surface that.
    """

    translation: Any
    language: str
    requested_language: str

    @property
    def translation_available(self) -> bool:
        return self.language == self.requested_language


def get_translation(obj, requested_language: str) -> ResolvedTranslation:
    """The one shared entrypoint every serializer should use. `obj` must
    have had its `translations` prefetched (Prefetch or prefetch_related)
    -- this never issues its own query."""
    translations = list(obj.translations.all())
    translation, used_language = pick_translation(translations, requested_language)
    return ResolvedTranslation(
        translation=translation, language=used_language, requested_language=requested_language
    )
