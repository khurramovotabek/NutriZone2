"""Celery tasks shared across the project (health checks, common utilities).

Domain-specific tasks (OTP sending, cashback crediting, order notifications,
etc.) live in each domain's own tasks.py, added in their respective phases.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="shared.ping")
def ping() -> str:
    """Trivial task used to verify the Celery worker + broker are wired up
    correctly (e.g. `docker compose exec backend celery -A config call shared.ping`)."""
    logger.info("pong")
    return "pong"
