from uuid import UUID

from django.conf import settings
from notifications_python_client import NotificationsAPIClient
from notifications_python_client.errors import HTTPError

from config.celery import app


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


@app.task
def send_email(template_id: UUID, personalisation: dict, email_address: str) -> dict:
    client = get_gov_notify_client()
    return client.send_email_notification(
        email_address, str(template_id), personalisation=personalisation
    )
