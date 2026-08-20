import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base model providing a UUID primary key and timestamps.

    Every domain model in the project inherits from this so that:
    - Primary keys are UUIDs (non-guessable, safe to expose in APIs).
    - created_at / updated_at are tracked consistently everywhere.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SortableModel(models.Model):
    """Abstract mixin adding a manual sort order field."""

    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
