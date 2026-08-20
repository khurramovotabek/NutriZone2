"""Signal handlers for the products domain.

No signals are wired yet. The natural future use here is cache invalidation
(e.g. bust a cached product-detail response when a Product/ProductVariant is
saved) once selectors.py starts caching read-heavy queries -- intentionally
not added speculatively before that caching exists.
"""
