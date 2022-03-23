import datetime
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from web.domains.case._import.wood.models import WoodQuotaChecklist
from web.domains.case.models import (
    CaseDocumentReference,
    CaseLicenceCertificateBase,
    UpdateRequest,
    VariationRequest,
)
from web.domains.case.shared import ImpExpStatus
from web.flow.errors import ProcessStateError
from web.flow.models import Task
from web.models import Country
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS, check_page_errors, check_pages_checked
from web.utils.validation import ApplicationErrors

if TYPE_CHECKING:
    from django.test.client import Client

    from web.domains.case._import.wood.models import WoodQuotaApplication


@pytest.fixture
def wood_application(icms_admin_client, wood_app_submitted):
    """A submitted wood application owned by the ICMS admin user."""
    icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    wood_app_submitted.refresh_from_db()
    licence = wood_app_submitted.get_most_recent_licence()
    licence.issue_paper_licence_only = True
    licence.save()

    return wood_app_submitted


@pytest.fixture
def com_app(icms_admin_client, com_app_submitted):
    """A submitted com application owned by the ICMS admin user."""
    icms_admin_client.post(CaseURLS.take_ownership(com_app_submitted.pk, case_type="export"))
    com_app_submitted.refresh_from_db()

    return com_app_submitted


def test_take_ownership(icms_admin_client: "Client", wood_app_submitted):
    resp = icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    assert resp.status_code == 302

    wood_app_submitted.refresh_from_db()
    assert wood_app_submitted.get_task(ImpExpStatus.PROCESSING, Task.TaskType.PROCESS)


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

    assert wood_application.status == ImpExpStatus.STOPPED


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
        expected_state=ImpExpStatus.PROCESSING, task_type=Task.TaskType.AUTHORISE
    )
    assert current_task is not None

    licence_doc = wood_application.get_most_recent_licence().document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )
    assert licence_doc.reference == "0000001B"


def test_start_authorisation_approved_application_has_no_errors_export_app(
    icms_admin_client, com_app
):
    com_app.decision = com_app.APPROVE
    com_app.save()

    # Clear any countries and set them here to test the references
    com_app.countries.all().delete()
    finland = Country.objects.get(name="Finland")
    germany = Country.objects.get(name="Germany")
    poland = Country.objects.get(name="Poland")
    com_app.countries.add(finland, germany, poland)

    # start authorisation should clear any document_references
    # create a dummy one here to test it.
    cert = com_app.get_most_recent_certificate()
    dr = cert.document_references.create(document_type=CaseDocumentReference.Type.CERTIFICATE)
    pk_to_delete = dr.id

    response = icms_admin_client.get(CaseURLS.authorise_application(com_app.pk, case_type="export"))
    assert response.status_code == 200
    errors: ApplicationErrors = response.context["errors"]
    assert errors is None

    # Now start authorisation
    response = icms_admin_client.post(
        CaseURLS.authorise_application(com_app.pk, case_type="export")
    )

    assertRedirects(response, reverse("workbasket"), 302)

    com_app.refresh_from_db()

    current_task = com_app.get_task(
        expected_state=ImpExpStatus.PROCESSING, task_type=Task.TaskType.AUTHORISE
    )
    assert current_task is not None

    cert = com_app.get_most_recent_certificate()

    assert cert.status == CaseLicenceCertificateBase.Status.DRAFT
    assert cert.document_references.count() == 3

    # Check the correct document references have been created
    finland_dr = cert.document_references.get(
        document_type=CaseDocumentReference.Type.CERTIFICATE, reference_data__country=finland
    )
    germany_dr = cert.document_references.get(
        document_type=CaseDocumentReference.Type.CERTIFICATE, reference_data__country=germany
    )
    poland_dr = cert.document_references.get(
        document_type=CaseDocumentReference.Type.CERTIFICATE, reference_data__country=poland
    )

    this_year = datetime.date.today().year
    assert finland_dr.reference == f"COM/{this_year}/00001"
    assert germany_dr.reference == f"COM/{this_year}/00002"
    assert poland_dr.reference == f"COM/{this_year}/00003"

    # explicitly check the old case_reference is gone
    assert not cert.document_references.filter(pk=pk_to_delete).exists()


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
        expected_state=ImpExpStatus.COMPLETED, task_type=Task.TaskType.REJECTED
    )
    assert current_task is not None

    assert wood_application.licences.count() == 1
    assert wood_application.licences.filter(
        status=CaseLicenceCertificateBase.Status.ARCHIVED
    ).exists()


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

    licence_doc = wood_application.get_most_recent_licence().document_references.get(
        document_type=CaseDocumentReference.Type.LICENCE
    )
    assert licence_doc.reference == "0000001B"


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
    assert wood_application.get_active_task_list() == []

    vr = wood_application.variation_requests.first()
    assert vr.status == VariationRequest.REJECTED
    assert vr.reject_cancellation_reason == "test refuse reason"
    assert vr.closed_datetime.date() == timezone.now().date()

    assert wood_application.licences.count() == 1
    assert wood_application.licences.filter(
        status=CaseLicenceCertificateBase.Status.ARCHIVED
    ).exists()


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

        licence = self.wood_app.get_most_recent_licence()
        assert licence.status == CaseLicenceCertificateBase.Status.DRAFT

    def test_authorise_post_valid(self):
        post_data = {"password": "test"}
        resp = self.client.post(CaseURLS.authorise_documents(self.wood_app.pk), post_data)

        assertRedirects(resp, reverse("workbasket"), status_code=302)

        self.wood_app.refresh_from_db()

        self.wood_app.check_expected_status([ImpExpStatus.COMPLETED])
        self.wood_app.get_expected_task(Task.TaskType.ACK)

        latest_licence = self.wood_app.get_most_recent_licence()
        assert latest_licence.status == CaseLicenceCertificateBase.Status.ACTIVE

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

        latest_licence = self.wood_app.get_most_recent_licence()
        assert latest_licence.status == CaseLicenceCertificateBase.Status.ACTIVE

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

        # Latest licence is still draft until after chief submission.
        latest_licence = self.wood_app.get_most_recent_licence()
        assert latest_licence.status == CaseLicenceCertificateBase.Status.DRAFT


def _set_valid_licence(wood_application):
    licence = wood_application.get_most_recent_licence()
    licence.licence_start_date = datetime.date.today()
    licence.licence_end_date = datetime.date(datetime.date.today().year + 1, 12, 1)
    licence.issue_paper_licence_only = True
    licence.save()


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
