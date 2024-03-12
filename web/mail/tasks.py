import datetime as dt

from django.contrib.postgres.aggregates import StringAgg
from django.utils import timezone

from config.celery import app
from web.domains.case.types import Authority
from web.models import (
    Constabulary,
    FirearmsAuthority,
    Importer,
    Mailshot,
    Section5Authority,
)

from .constants import (
    CELERY_MAIL_QUEUE_NAME,
    SEND_AUTHORITY_EXPIRING_FIREARMS_TASK_NAME,
    SEND_AUTHORITY_EXPIRING_SECTION_5_TASK_NAME,
    SEND_MAILSHOT_TASK_NAME,
    SEND_RETRACT_MAILSHOT_TASK_NAME,
)
from .emails import (
    send_authority_expiring_firearms_email,
    send_authority_expiring_section_5_email,
    send_mailshot_email,
    send_retract_mailshot_email,
)
from .types import ImporterDetails


@app.task(name=SEND_MAILSHOT_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_mailshot_email_task(mailshot_pk: int):
    mailshot = Mailshot.objects.get(pk=mailshot_pk)
    send_mailshot_email(mailshot)


@app.task(name=SEND_RETRACT_MAILSHOT_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_retract_mailshot_email_task(mailshot_pk: int):
    mailshot = Mailshot.objects.get(pk=mailshot_pk)
    send_retract_mailshot_email(mailshot)


@app.task(name=SEND_AUTHORITY_EXPIRING_SECTION_5_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_authority_expiring_section_5_email_task():
    expiry_date = timezone.now().date() + dt.timedelta(days=30)
    importers = get_expiring_importers_details(Section5Authority, expiry_date, None)
    if importers:
        send_authority_expiring_section_5_email(importers, expiry_date)


@app.task(name=SEND_AUTHORITY_EXPIRING_FIREARMS_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_authority_expiring_firearms_email_task():
    expiry_date = timezone.now().date() + dt.timedelta(days=30)
    constabularies = Constabulary.objects.filter(
        firearmsauthority__end_date=expiry_date, is_active=True
    ).distinct()
    for constabulary in constabularies:
        importers = get_expiring_importers_details(FirearmsAuthority, expiry_date, constabulary)
        if importers:
            send_authority_expiring_firearms_email(importers, expiry_date, constabulary)


def get_expiring_importers_details(
    authority_class: type[Authority], expiry_date: dt.date, constabulary: Constabulary | None
) -> list[ImporterDetails]:
    authority_type = authority_class.AUTHORITY_TYPE.replace(" ", "").lower()
    importer_filter = {
        f"{authority_type}_authorities__end_date": expiry_date,
        "is_active": True,
        f"{authority_type}_authorities__is_active": True,
    }
    if constabulary:
        importer_filter[f"{authority_type}_authorities__issuing_constabulary"] = constabulary
    reference_field = f"{authority_type}_authorities__reference"
    return list(
        Importer.objects.filter(**importer_filter)
        .annotate(
            authority_refs=StringAgg(reference_field, delimiter=", ", ordering=reference_field)
        )
        .order_by("name")
        .values("id", "name", "authority_refs")
    )
