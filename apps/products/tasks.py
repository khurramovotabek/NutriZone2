"""Celery tasks for the products domain.

No async tasks needed yet -- product writes are cheap enough to happen
synchronously in the request/response cycle. A likely future addition is a
scheduled task to recompute "low stock" flags or sync prices from a supplier
feed via apps.integrations.
"""
