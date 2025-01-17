import datetime as dt

from django.contrib.sites.models import Site
from django.db.models import F, QuerySet
from django.utils import timezone

from web.auth.backends import ANONYMOUS_USER_PK
from web.mail.emails import send_email_verification_email
from web.models import Email, EmailVerification, User


def user_list_view_qs() -> QuerySet[User]:
    """Reusable QuerySet that can be used in several views."""
    return User.objects.exclude(pk=ANONYMOUS_USER_PK).exclude(is_superuser=True)


def send_and_create_email_verification(email: Email, site: Site) -> None:
    verification, created = EmailVerification.objects.get_or_create(email=email, processed=False)

    if created:
        _increment_verified_reminder_count(email)
    # Created older than 2 weeks
    elif verification.created_at < (timezone.now() - dt.timedelta(weeks=2)):
        verification.processed = True
        verification.save()

        verification = EmailVerification.objects.create(email=email)
        _increment_verified_reminder_count(email)

    email.refresh_from_db()
    if email.verified_reminder_count <= 5:
        send_email_verification_email(verification, site)
    else:
        # Reset this just in case the user tries to enable portal notifications again for this email
        email.verified_reminder_count = 0
        email.portal_notifications = False
        email.save()

        # Set the EmailVerification record to processed as it won't ever be used.
        verification.processed = True
        verification.save()


def _increment_verified_reminder_count(email: Email) -> None:
    email.verified_reminder_count = F("verified_reminder_count") + 1
    email.save()
