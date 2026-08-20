"""
Celery application entrypoint.

Workers are started with `celery -A config worker`, beat with
`celery -A config beat` (see docker-compose.yml). Task modules are
auto-discovered from each app's tasks.py.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("nutrizone")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
