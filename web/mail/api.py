from uuid import UUID

from celery.app.task import Task
from django.conf import settings
from notifications_python_client import NotificationsAPIClient
from notifications_python_client.errors import HTTPError

from config.celery import app
from web.utils.sentry import capture_exception

from .constants import CELERY_MAIL_QUEUE_NAME, SEND_EMAIL_TASK_NAME


class SendEmailTask(Task):
    """
    GOV NOTIFY LIMITS

    3000 Messages per minute
    250,000 emails per day

    rate_limit = "1000/m"

    Prioritises new sends over retries
    """

    autoretry_for = [HTTPError]
    max_retries = settings.MAIL_TASK_MAX_RETRIES
    retry_backoff = 10
    retry_jitter = settings.MAIL_TASK_RETRY_JITTER
    rate_limit = settings.MAIL_TASK_RATE_LIMIT

    def retry(self, *args, **kwargs):
        try:
            super().retry(*args, **kwargs)
        except HTTPError as e:
            capture_exception()
            raise e


def get_gov_notify_client() -> NotificationsAPIClient:
    return NotificationsAPIClient(settings.GOV_NOTIFY_API_KEY)


def get_template_by_id(template_id: UUID) -> dict:
    client = get_gov_notify_client()
    try:
        return client.get_template(template_id)
    except HTTPError as e:
        return e.response.json()


def is_valid_template_id(template_id: UUID) -> bool:
    response = get_template_by_id(template_id)
    gov_notify_template_id = response.get("id", "")
    try:
        gov_notify_template_id = UUID(gov_notify_template_id)
    except ValueError:
        return False
    return gov_notify_template_id == template_id


@app.task(base=SendEmailTask, name=SEND_EMAIL_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_email(template_id: UUID, personalisation: dict, email_address: str) -> dict:
    client = get_gov_notify_client()
    return client.send_email_notification(
        email_address, str(template_id), personalisation=personalisation
    )
