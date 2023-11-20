import logging

from config.celery import app

# Celery tasks
from web.domains.case.tasks import (  # NOQA
    create_document_pack_on_error,
    create_document_pack_on_success,
    create_export_application_document,
    create_import_application_document,
)
from web.mail.tasks import (  # NOQA
    send_authority_expiring_firearms_email_task,
    send_authority_expiring_section_5_email_task,
    send_mailshot_email_task,
    send_retract_mailshot_email_task,
)

logger = logging.getLogger(__name__)


# Test Task
@app.task(name="web.tasks.check_celery_beat_running")
def check_celery_beat_running() -> None:
    logger.debug("Celery beat test task working correctly.")
