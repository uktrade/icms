#!/usr/bin/env python

import os

from celery import Celery
from celery.schedules import crontab

from web.mail.constants import SEND_AUTHORITY_EXPIRING_SECTION_5_TASK_NAME

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("icms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Only enable when constabulary contacts manage firearms authorities
    # "authority_expiring_firearms_email": {
    #     "task": SEND_AUTHORITY_EXPIRING_FIREARMS_TASK_NAME,
    #     "schedule": crontab(hour=7),
    # },
    "authority_expiring_section_5_email": {
        "task": SEND_AUTHORITY_EXPIRING_SECTION_5_TASK_NAME,
        "schedule": crontab(hour=7),
    },
}
