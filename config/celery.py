#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("icms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
