import datetime
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from web.domains.case._import.models import ImportApplication
from web.domains.case._import.wood.models import WoodQuotaChecklist
from web.domains.case.models import UpdateRequest, VariationRequest
from web.domains.case.shared import ImpExpStatus
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
    _set_valid_licence(wood_application)

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


def test_start_authorisation_approved_variation_requested_application(
    icms_admin_client, wood_application, test_icms_admin_user
):
    """Test an approved variation requested application ends in the correct status & has the correct task"""
    wood_application.decision = wood_application.APPROVE
    _set_valid_licence(wood_application)
    _add_valid_checklist(wood_application)

    # Set the variation fields
    wood_application.status = ImpExpStatus.VARIATION_REQUESTED
    wood_application.variation_decision = wood_application.APPROVE
    _add_variation_request(wood_application, test_icms_admin_user)

    wood_application.save()

    # Now start authorisation
    response = icms_admin_client.post(CaseURLS.authorise_application(wood_application.pk))
    assertRedirects(response, reverse("workbasket"), 302)
    wood_application.refresh_from_db()

    wood_application.check_expected_status([ImpExpStatus.VARIATION_REQUESTED])
    expected_task = wood_application.get_expected_task(Task.TaskType.AUTHORISE)
    vr = wood_application.variation_requests.first()
    assert vr.status == VariationRequest.OPEN

    assert expected_task is not None


def test_start_authorisation_rejected_variation_requested_application(
    icms_admin_client, wood_application, test_icms_admin_user
):
    """Test an rejected variation requested application ends in the correct status & has the correct task"""
    wood_application.decision = wood_application.APPROVE
    _set_valid_licence(wood_application)
    _add_valid_checklist(wood_application)

    # Set the variation fields
    wood_application.status = ImpExpStatus.VARIATION_REQUESTED
    wood_application.variation_decision = wood_application.REFUSE
    wood_application.variation_refuse_reason = "test refuse reason"
    _add_variation_request(wood_application, test_icms_admin_user)

    wood_application.save()

    # Now start authorisation
    response = icms_admin_client.post(CaseURLS.authorise_application(wood_application.pk))
    assertRedirects(response, reverse("workbasket"), 302)
    wood_application.refresh_from_db()

    wood_application.check_expected_status([ImpExpStatus.COMPLETED])
    expected_task = wood_application.get_expected_task(Task.TaskType.ACK)
    vr = wood_application.variation_requests.first()
    assert vr.status == VariationRequest.REJECTED
    assert vr.reject_cancellation_reason == "test refuse reason"
    assert vr.closed_datetime.date() == timezone.now().date()

    assert expected_task is not None


class TestAuthoriseDocumentsView:
    needed_task = Task.TaskType.AUTHORISE
    needed_status = [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]

    form_data = {"password": "test"}

    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, wood_app_submitted):
        """Using the submitted app override the app to the state we want."""

        wood_app_submitted.status = ImpExpStatus.PROCESSING
        wood_app_submitted.save()

        task = wood_app_submitted.tasks.get(is_active=True)
        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(
            process=wood_app_submitted, task_type=Task.TaskType.AUTHORISE, previous=task
        )

        self.wood_app = wood_app_submitted

    def test_authorise_post_valid(self):
        post_data = {"password": "test"}
        resp = self.client.post(CaseURLS.authorise_documents(self.wood_app.pk), post_data)

        assertRedirects(resp, reverse("workbasket"), status_code=302)

        self.wood_app.refresh_from_db()

        self.wood_app.check_expected_status([ImpExpStatus.COMPLETED])
        self.wood_app.get_expected_task(Task.TaskType.ACK)

    def test_authorise_variation_request_post_valid(self, test_icms_admin_user):
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        _add_variation_request(self.wood_app, test_icms_admin_user)
        self.wood_app.save()

        post_data = {"password": "test"}
        resp = self.client.post(CaseURLS.authorise_documents(self.wood_app.pk), post_data)

        assertRedirects(resp, reverse("workbasket"), status_code=302)

        self.wood_app.refresh_from_db()

        self.wood_app.check_expected_status([ImpExpStatus.COMPLETED])
        self.wood_app.get_expected_task(Task.TaskType.ACK)

        vr = self.wood_app.variation_requests.first()
        assert vr.status == VariationRequest.ACCEPTED

    def test_authorise_post_valid_for_app_requiring_chief(self):
        # Override the chief flag for the wood quota application type to send to chief.
        iat = self.wood_app.application_type
        iat.chief_flag = True
        iat.save()

        post_data = {"password": "test"}
        resp = self.client.post(CaseURLS.authorise_documents(self.wood_app.pk), post_data)

        assertRedirects(resp, reverse("workbasket"), status_code=302)

        self.wood_app.refresh_from_db()

        self.wood_app.check_expected_status([ImpExpStatus.PROCESSING])
        self.wood_app.get_expected_task(Task.TaskType.CHIEF_WAIT)


class TestManageVariationsView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, wood_app_submitted):
        self.wood_app = wood_app_submitted

    def test_get_variations(self, test_icms_admin_user):
        self.client.post(CaseURLS.take_ownership(self.wood_app.pk))

        # Add a few previous variation requests
        _add_variation_request(self.wood_app, test_icms_admin_user, VariationRequest.REJECTED)
        _add_variation_request(self.wood_app, test_icms_admin_user, VariationRequest.ACCEPTED)
        # Add an open one last (as it's the latest)
        _add_variation_request(self.wood_app, test_icms_admin_user, VariationRequest.OPEN)

        response = self.client.get(CaseURLS.manage_variations(self.wood_app.pk))
        assert response.status_code == 200

        cd = response.context_data
        vrs = cd["variation_requests"]

        expected_status_order = [
            VariationRequest.OPEN,
            VariationRequest.ACCEPTED,
            VariationRequest.REJECTED,
        ]

        assert expected_status_order == [vr.status for vr in vrs]


# TODO: Write tests for this view.
class TestCancelVariationRequestView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, test_icms_admin_user):
        self.wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        _add_variation_request(self.wood_app, test_icms_admin_user)
        self.wood_app.save()

    def test_cancel_variation_request_get(self):
        vr = self.wood_app.variation_requests.first()
        resp = self.client.get(CaseURLS.cancel_variation_request(self.wood_app.pk, vr.pk))

        cd = resp.context_data

        assert resp.status_code == 200
        assert cd["object"] == vr
        assert cd["process"] == self.wood_app
        assert cd["page_title"] == f"Variations {self.wood_app.get_reference()}"
        assert cd["case_type"] == "import"

    def test_cancel_variation_request_post(self, test_icms_admin_user):
        vr = self.wood_app.variation_requests.first()
        resp = self.client.post(
            CaseURLS.cancel_variation_request(self.wood_app.pk, vr.pk),
            {"reject_cancellation_reason": "Test cancellation reason"},
        )

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()
        vr.refresh_from_db()

        assert vr.status == VariationRequest.CANCELLED
        assert vr.reject_cancellation_reason == "Test cancellation reason"
        assert vr.closed_by == test_icms_admin_user
        assert vr.closed_datetime.date() == timezone.now().date()

        self.wood_app.check_expected_status([ImpExpStatus.COMPLETED])
        self.wood_app.get_expected_task(Task.TaskType.ACK, select_for_update=False)


def _set_valid_licence(wood_application):
    wood_application.licence_start_date = datetime.date.today()
    wood_application.licence_end_date = datetime.date(datetime.date.today().year + 1, 12, 1)


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


def _add_variation_request(wood_application, user, status=VariationRequest.OPEN):
    wood_application.variation_requests.create(
        status=status,
        what_varied="Dummy what_varied",
        why_varied="Dummy why_varied",
        when_varied=timezone.now().date(),
        requested_by=user,
    )
