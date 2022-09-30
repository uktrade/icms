import datetime

import pytest
from django.utils import timezone

from web.domains.case.shared import ImpExpStatus
from web.models import (
    CaseDocumentReference,
    Country,
    ImportApplicationLicence,
    ImportApplicationType,
    LiteHMRCChiefRequest,
    SILApplication,
    Task,
)


@pytest.fixture
def _fa_sil(db, test_import_user, importer, office):
    """Fake FA-SIL app to test CHIEF code"""

    app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type="FA", sub_type="SIL"),
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        status=ImpExpStatus.PROCESSING,
        reference="IMI/2022/12345",
        # data for getting the serializer to work
        origin_country=Country.objects.get(name="Germany"),
    )

    # Current draft licence
    licence = app.licences.create(
        licence_start_date=datetime.date.today(),
        licence_end_date=datetime.date(datetime.date.today().year + 1, 12, 1),
        status=ImportApplicationLicence.Status.DRAFT,
    )
    licence.document_references.create(
        document_type=CaseDocumentReference.Type.LICENCE, reference="dummy-reference"
    )

    return app


@pytest.fixture
def fa_sil_app_doc_signing(_fa_sil: SILApplication) -> SILApplication:
    """Application that has had its documents signed and is waiting to be sent to chief."""

    app = _fa_sil

    app.tasks.create(task_type=Task.TaskType.DOCUMENT_SIGNING)

    return app


@pytest.fixture
def fa_sil_app_with_chief(_fa_sil: SILApplication) -> SILApplication:
    """Dummy application that has been sent to chief"""
    app = _fa_sil

    # Current active task
    app.tasks.create(task_type=Task.TaskType.CHIEF_WAIT)

    LiteHMRCChiefRequest.objects.create(
        import_application=app,
        case_reference=app.reference,
        request_data={"foo": "bar"},
        request_sent_datetime=timezone.now(),
    )

    return app


def check_licence_approve_correct(
    app: SILApplication, licence: ImportApplicationLicence, chief_wait_task: Task
) -> None:
    app.refresh_from_db()
    licence.refresh_from_db()
    chief_wait_task.refresh_from_db()

    # Check CHIEF_WAIT task is finished
    assert not chief_wait_task.is_active

    # Check app is complete
    assert app.status == ImpExpStatus.COMPLETED

    # Check licence is active
    assert licence.status == ImportApplicationLicence.Status.ACTIVE

    # Check licence reference matches current app case reference
    assert app.reference == licence.case_reference


def check_licence_reject_correct(
    app: SILApplication, licence: ImportApplicationLicence, chief_wait_task: Task
) -> None:
    app.refresh_from_db()
    licence.refresh_from_db()
    chief_wait_task.refresh_from_db()

    # The app status is still processing
    assert app.status == ImpExpStatus.PROCESSING

    # Check CHIEF_WAIT task is finished
    assert not chief_wait_task.is_active

    # Check the current task is chief error
    app.get_expected_task(Task.TaskType.CHIEF_ERROR, select_for_update=False)


def check_complete_chief_request_correct(chief_request: LiteHMRCChiefRequest) -> None:
    chief_request.refresh_from_db()

    assert chief_request.status == LiteHMRCChiefRequest.CHIEFStatus.SUCCESS
    assert chief_request.request_sent_datetime < chief_request.response_received_datetime


def check_fail_chief_request_correct(chief_request: LiteHMRCChiefRequest) -> None:
    chief_request.refresh_from_db()

    assert chief_request.status == LiteHMRCChiefRequest.CHIEFStatus.ERROR
    assert chief_request.request_sent_datetime < chief_request.response_received_datetime
    assert chief_request.response_error_code == "1"
    assert chief_request.response_error_msg == "Test error message"
