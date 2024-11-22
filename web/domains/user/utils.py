from django.contrib.sites.models import Site
from django.db.models import QuerySet

from web.auth.backends import ANONYMOUS_USER_PK
from web.mail.emails import send_email_verification_email
from web.models import Email, EmailVerification, User


def user_list_view_qs() -> QuerySet[User]:
    """Reusable QuerySet that can be used in several views."""
    return User.objects.exclude(pk=ANONYMOUS_USER_PK).exclude(is_superuser=True)


def send_and_create_email_verification(email: Email, site: Site) -> None:
    verification = EmailVerification.objects.create(email=email)
    send_email_verification_email(verification, site)
