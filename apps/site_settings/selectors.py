"""Read-query helpers for site settings.

The singleton-row pattern is handled by SiteSettings.load() on the model
itself (see models.py) since it's identity resolution, not a query variant.
"""
