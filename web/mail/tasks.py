from config.celery import app
from web.models import Mailshot

from .constants import (
    CELERY_MAIL_QUEUE_NAME,
    SEND_MAILSHOT_TASK_NAME,
    SEND_RETRACT_MAILSHOT_TASK_NAME,
)
from .emails import send_mailshot_email, send_retract_mailshot_email


@app.task(name=SEND_MAILSHOT_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_mailshot_email_task(mailshot_pk: int):
    mailshot = Mailshot.objects.get(pk=mailshot_pk)
    send_mailshot_email(mailshot)


@app.task(name=SEND_RETRACT_MAILSHOT_TASK_NAME, queue=CELERY_MAIL_QUEUE_NAME)
def send_retract_mailshot_email_task(mailshot_pk: int):
    mailshot = Mailshot.objects.get(pk=mailshot_pk)
    send_retract_mailshot_email(mailshot)
