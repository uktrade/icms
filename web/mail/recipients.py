from django.db.models import QuerySet

from web.mail.decorators import override_recipients
from web.models import User
from web.notify.utils import get_notification_emails
from web.permissions import get_ilb_case_officers


def get_ilb_case_officers_email_addresses() -> list[str]:
    users = get_ilb_case_officers()
    return get_email_addresses_for_users(users)


@override_recipients
def get_email_addresses_for_users(users: QuerySet[User]) -> list[str]:
    emails = []
    for user in users:
        emails.extend(get_notification_emails(user))
    return list(set(emails))
