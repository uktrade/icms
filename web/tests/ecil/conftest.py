import pytest

from web.domains.case.services import case_progress
from web.domains.case.services.application import create_export_application
from web.domains.case.shared import ImpExpStatus
from web.models import CertificateOfFreeSaleApplication, ExportApplicationType, Task


@pytest.fixture()
def prototype_cfs_app_in_progress(
    rf,
    prototype_export_user,
    exporter,
    exporter_office,
) -> CertificateOfFreeSaleApplication:
    """Create a basic in progress CFS app with no fields populated."""

    app_type = ExportApplicationType.objects.get(type_code=ExportApplicationType.Types.FREE_SALE)
    rf.user = prototype_export_user
    app = create_export_application(
        request=rf,
        model_class=CertificateOfFreeSaleApplication,
        application_type=app_type,
        exporter=exporter,
        exporter_office=exporter_office,
    )

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app
