import datetime
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from web.domains.case._import.models import ImportApplication
from web.domains.case._import.wood.models import WoodQuotaChecklist
from web.domains.case.models import UpdateRequest
from web.flow.errors import ProcessStateError
from web.flow.models import Task
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS, check_page_errors, check_pages_checked
from web.utils.validation import ApplicationErrors

if TYPE_CHECKING:
    from django.test.client import Client

    from web.domains.case._import.wood.models import WoodQuotaApplication


@pytest.fixture
def wood_application(icms_admin_client, wood_app_submitted):
    """A submitted application owned by the ICMS admin user."""
    icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    wood_app_submitted.refresh_from_db()

    return wood_app_submitted


def test_take_ownership(icms_admin_client: "Client", wood_app_submitted):
    resp = icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    assert resp.status_code == 302

    wood_app_submitted.refresh_from_db()
    assert wood_app_submitted.get_task(ImportApplication.Statuses.PROCESSING, Task.TaskType.PROCESS)


def test_take_ownership_in_progress(icms_admin_client: "Client", wood_app_in_progress):
    # Can't own an in progress application
    with pytest.raises(ProcessStateError):
        icms_admin_client.post(CaseURLS.take_ownership(wood_app_in_progress.pk))


def test_manage_case_get(icms_admin_client: "Client", wood_application):
    resp = icms_admin_client.get(CaseURLS.manage(wood_application.pk))

    assert resp.status_code == 200
    assertContains(resp, "Wood (Quota) - Manage")
    assertTemplateUsed(resp, "web/domains/case/manage/manage.html")


def test_manage_case_close_case(icms_admin_client: "Client", wood_application):

    post_data = {"send_email": False}
    resp = icms_admin_client.post(CaseURLS.close_case(wood_application.pk), post_data)
    assertRedirects(resp, reverse("workbasket"), status_code=302)

    wood_application.refresh_from_db()

    assert wood_application.status == wood_application.Statuses.STOPPED


def test_manage_withdrawals_get(
    icms_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
):
    resp = icms_admin_client.get(CaseURLS.manage_withdrawals(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Withdrawals")
    assertTemplateUsed(resp, "web/domains/case/manage/withdrawals.html")

    assert resp.context["withdrawals"].count() == 0
    assert resp.context["current_withdrawal"] is None


# def test_manage_withdrawals_post():
#     # TODO: Add test for approving a withdrawal
#     # TODO: Add test to reject a withdrawal
#     ...


def test_start_authorisation_approved_application_has_errors(icms_admin_client, wood_application):
    """Test start authorisation catches the correct errors for an approved application."""

    wood_application.decision = wood_application.APPROVE
    # Create an open update request
    wood_application.update_requests.create(status=UpdateRequest.Status.OPEN)
    wood_application.save()

    response = icms_admin_client.get(CaseURLS.authorise_application(wood_application.pk))
    assert response.status_code == 200

    errors: ApplicationErrors = response.context["errors"]
    assert errors.has_errors()

    check_pages_checked(errors, ["Checklist", "Response Preparation", "Application Updates"])

    check_page_errors(errors, "Checklist", ["Checklist"])
    check_page_errors(errors, "Response Preparation", ["Licence end date"])
    check_page_errors(errors=errors, page_name="Application Updates", error_field_names=["Status"])


def test_start_authorisation_approved_application_has_no_errors(
    icms_admin_client, wood_application
):
    """Test a valid approved application ends in the correct state."""

    wood_application.decision = wood_application.APPROVE

    # Set licence details
    wood_application.licence_start_date = datetime.date.today()
    wood_application.licence_end_date = datetime.date(datetime.date.today().year + 1, 12, 1)
    wood_application.save()

    # Create the checklist (fully valid)
    _add_valid_checklist(wood_application)
    wood_application.save()

    response = icms_admin_client.get(CaseURLS.authorise_application(wood_application.pk))
    assert response.status_code == 200
    errors: ApplicationErrors = response.context["errors"]
    assert errors is None

    # Now start authorisation
    response = icms_admin_client.post(CaseURLS.authorise_application(wood_application.pk))

    assertRedirects(response, reverse("workbasket"), 302)

    wood_application.refresh_from_db()

    current_task = wood_application.get_task(
        expected_state=ImportApplication.Statuses.PROCESSING, task_type=Task.TaskType.AUTHORISE
    )
    assert current_task is not None


def test_start_authorisation_refused_application_has_errors(icms_admin_client, wood_application):
    """Test start authorisation catches the correct errors for a refused application."""

    wood_application.decision = wood_application.REFUSE
    wood_application.save()

    response = icms_admin_client.get(CaseURLS.authorise_application(wood_application.pk))
    assert response.status_code == 200

    errors: ApplicationErrors = response.context["errors"]
    assert errors.has_errors()

    check_page_errors(errors, "Checklist", ["Checklist"])


def test_start_authorisation_refused_application_has_no_errors(icms_admin_client, wood_application):
    """Test a valid refused application ends in the correct state."""

    wood_application.decision = wood_application.REFUSE
    _add_valid_checklist(wood_application)
    wood_application.save()

    response = icms_admin_client.get(CaseURLS.authorise_application(wood_application.pk))
    assert response.status_code == 200

    errors: ApplicationErrors = response.context["errors"]
    assert errors is None

    # Now start authorisation
    response = icms_admin_client.post(CaseURLS.authorise_application(wood_application.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    wood_application.refresh_from_db()

    current_task = wood_application.get_task(
        expected_state=ImportApplication.Statuses.COMPLETED, task_type=Task.TaskType.REJECTED
    )
    assert current_task is not None


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
