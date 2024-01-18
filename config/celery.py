import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

from web.mail.constants import SEND_AUTHORITY_EXPIRING_SECTION_5_TASK_NAME

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("icms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.APP_ENV == "production":
        schedule = get_icms_prod_beat_schedule()
    else:
        schedule = get_imcs_dev_beat_schedule()

    app.conf.beat_schedule = schedule


def get_icms_prod_beat_schedule():
    """Production beat schedule used when configured to run for IMCS."""

    return {
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


def get_imcs_dev_beat_schedule():
    """Non production beat schedule.

    This schedule contains a task to test the beat schedule is working.
    """

    return {
        "check_celery_beat_running": {
            "task": "web.tasks.check_celery_beat_running",
            "schedule": crontab(minute="*/15"),
        },
    }
