import pytest

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import CertificateOfFreeSaleApplication, ExportApplicationType, Task
from web.tests.application_utils import create_export_app


@pytest.fixture()
def prototype_cfs_app_in_progress(
    prototype_export_client, exporter, exporter_office, prototype_export_user
) -> CertificateOfFreeSaleApplication:
    """Create a basic in progress CFS app with no fields populated."""

    # Only links the cfs record will are the exporter and office links.
    app_pk = create_export_app(
        client=prototype_export_client,
        type_code=ExportApplicationType.Types.FREE_SALE,
        exporter_pk=exporter.pk,
        office_pk=exporter_office.pk,
    )
    app = CertificateOfFreeSaleApplication.objects.get(pk=app_pk)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app
