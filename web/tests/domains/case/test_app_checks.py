import datetime

import pytest

from web.domains.case._import.wood.models import (
    WoodQuotaApplication,
    WoodQuotaChecklist,
)
from web.domains.case.app_checks import get_app_errors
from web.domains.case.models import UpdateRequest
from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS, check_page_errors, check_pages_checked


@pytest.fixture
def wood_application(icms_admin_client, wood_app_submitted):
    """A submitted application owned by the ICMS admin user."""
    icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    wood_app_submitted.refresh_from_db()

    return wood_app_submitted


def test_get_app_errors_application_approved_no_errors(wood_application: WoodQuotaApplication):
    # Approve it
    wood_application.decision = wood_application.APPROVE
    wood_application.save()

    # Set licence details
    licence = document_pack.pack_draft_get(wood_application)
    licence.licence_start_date = datetime.date.today()
    licence.licence_end_date = datetime.date(datetime.date.today().year + 1, 12, 1)
    licence.save()

    # Create the checklist (fully valid)
    _add_valid_checklist(wood_application)

    errors = get_app_errors(wood_application, "import")

    assert not errors.has_errors()
    check_pages_checked(errors, ["Checklist", "Response Preparation", "Application Updates"])


def test_get_app_errors_application_refused_no_errors(wood_application: WoodQuotaApplication):
    # Refuse the application
    wood_application.decision = wood_application.REFUSE

    # Create the checklist (fully valid)
    _add_valid_checklist(wood_application)
    wood_application.save()

    errors = get_app_errors(wood_application, "import")

    assert not errors.has_errors()
    check_pages_checked(errors, ["Checklist"])


def test_get_app_errors_application_approved_has_errors(
    wood_application: WoodQuotaApplication,
):
    wood_application.decision = wood_application.APPROVE

    # Create an open update request
    wood_application.update_requests.create(status=UpdateRequest.Status.OPEN)

    wood_application.save()

    errors = get_app_errors(wood_application, "import")

    assert errors.has_errors()
    check_pages_checked(errors, ["Checklist", "Response Preparation", "Application Updates"])

    # Checklist must be completed
    check_page_errors(
        errors=errors,
        page_name="Checklist",
        error_field_names=["Checklist"],
    )

    # Licence details must be set
    check_page_errors(
        errors=errors,
        page_name="Response Preparation",
        error_field_names=["Licence end date"],
    )

    # Open update requests must be closed
    check_page_errors(
        errors=errors,
        page_name="Application Updates",
        error_field_names=["Status"],
    )


def test_get_app_errors_application_refused_has_errors(
    wood_application: WoodQuotaApplication,
):
    # Refuse the application
    wood_application.decision = wood_application.REFUSE
    wood_application.save()

    errors = get_app_errors(wood_application, "import")

    assert errors.has_errors()
    check_pages_checked(errors, ["Checklist"])

    # Checklist must be completed
    check_page_errors(
        errors=errors,
        page_name="Checklist",
        error_field_names=["Checklist"],
    )


def test_get_app_errors_application_approval_null_has_errors(
    wood_application: WoodQuotaApplication,
):
    errors = get_app_errors(wood_application, "import")

    assert errors.has_errors()
    check_pages_checked(errors, ["Checklist", "Response Preparation", "Application Updates"])

    # Checklist must be completed
    check_page_errors(
        errors=errors,
        page_name="Checklist",
        error_field_names=["Checklist"],
    )

    # Decision must be approved or refused
    check_page_errors(
        errors=errors,
        page_name="Response Preparation",
        error_field_names=["Decision"],
    )

    # No errors on this page.
    check_page_errors(
        errors=errors,
        page_name="Application Updates",
        error_field_names=[],
    )


def test_get_app_errors_application_approved_variation_requested(
    wood_application: WoodQuotaApplication,
):
    # Approve it / Set the application to be a variation request
    wood_application.decision = wood_application.APPROVE
    wood_application.status = ImpExpStatus.VARIATION_REQUESTED
    wood_application.save()

    # Set licence details
    licence = document_pack.pack_draft_get(wood_application)
    licence.licence_start_date = datetime.date.today()
    licence.licence_end_date = datetime.date(datetime.date.today().year + 1, 12, 1)
    licence.save()

    # Create the checklist (fully valid)
    _add_valid_checklist(wood_application)

    errors = get_app_errors(wood_application, "import")

    assert errors.has_errors()
    check_pages_checked(errors, ["Checklist", "Response Preparation", "Application Updates"])

    # Variation Decision needs setting:
    check_page_errors(
        errors=errors,
        page_name="Response Preparation",
        error_field_names=["Variation Decision"],
    )

    wood_application.variation_decision = WoodQuotaApplication.APPROVE
    wood_application.save()

    errors = get_app_errors(wood_application, "import")
    assert not errors.has_errors()


def _add_valid_checklist(wood_application):
    wood_application.checklist = WoodQuotaChecklist.objects.create(
        import_application=wood_application,
        case_update=YesNoNAChoices.yes,
        fir_required=YesNoNAChoices.yes,
        validity_period_correct=YesNoNAChoices.yes,
        endorsements_listed=YesNoNAChoices.yes,
        response_preparation=True,
        authorisation=True,
        sigl_wood_application_logged=True,
    )
