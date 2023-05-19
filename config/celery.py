#!/usr/bin/env python

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("icms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "firearms_authority_expiring": {
        "task": "web.notify.notify.send_firearms_authority_expiry_notification",
        "schedule": crontab(hour=7),
    },
    "section_5_expiring": {
        "task": "web.notify.notify.send_section_5_expiry_notification",
        "schedule": crontab(hour=7),
    },
}
