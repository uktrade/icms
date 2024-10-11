import datetime as dt

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import Commodity, ImportApplicationLicence, Task, WoodQuotaApplication
from web.models.shared import YesNoNAChoices
from web.tests.application_utils import (
    add_app_file,
    compare_import_application_with_fixture,
    create_import_app,
    save_app_data,
    submit_app,
)
from web.tests.helpers import CaseURLS
from web.utils.commodity import get_active_commodities


def test_create_in_progress_wood_application(
    importer_client, importer, office, importer_one_contact, wood_app_in_progress
):
    # Create the wood app
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-wood-quota",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    # Save a valid set of data.
    wood_commodities = get_active_commodities(Commodity.objects.filter(commodity_type__type="Wood"))
    form_data = {
        "contact": importer_one_contact.pk,
        "applicant_reference": "Wood App Reference",
        "shipping_year": dt.date.today().year,
        "exporter_name": "Some Exporter",
        "exporter_address": "Some Exporter Address",
        "exporter_vat_nr": "123456789",
        "commodity": wood_commodities.first().pk,
        "goods_description": "Very Woody",
        "goods_qty": 43,
        "goods_unit": "cubic metres",
        "additional_comments": "Nothing more to say",
    }
    save_app_data(
        client=importer_client, view_name="import:wood:edit", app_pk=app_pk, form_data=form_data
    )

    # Add a contract file to the wood app
    add_app_file(
        client=importer_client,
        view_name="import:wood:add-contract-document",
        app_pk=app_pk,
        post_data={"reference": "reference field", "contract_date": "09-Nov-2021"},
    )

    app = WoodQuotaApplication.objects.get(pk=app_pk)
    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    # Compare created application using views matches the test fixture
    compare_import_application_with_fixture(app, wood_app_in_progress, ["contract_documents"])

    # Compare files
    assert app.supporting_documents.count() == wood_app_in_progress.supporting_documents.count()
    assert app.contract_documents.count() == wood_app_in_progress.contract_documents.count()


def test_submit_wood_application(importer_client, wood_app_in_progress, wood_app_submitted):
    assert wood_app_in_progress.decision is None

    submit_app(
        client=importer_client, view_name="import:wood:submit-quota", app_pk=wood_app_in_progress.pk
    )

    wood_app_in_progress.refresh_from_db()

    case_progress.check_expected_status(wood_app_in_progress, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(wood_app_in_progress, Task.TaskType.PROCESS)

    # Compare created application using views matches the test fixture
    compare_import_application_with_fixture(
        wood_app_in_progress, wood_app_submitted, ["contract_documents", "reference"]
    )

    # Compare files
    assert (
        wood_app_in_progress.supporting_documents.count()
        == wood_app_submitted.supporting_documents.count()
    )
    assert (
        wood_app_in_progress.contract_documents.count()
        == wood_app_submitted.contract_documents.count()
    )

    # Check decision is approved
    assert wood_app_in_progress.decision == wood_app_in_progress.APPROVE


@pytest.fixture
def wood_application(ilb_admin_client, wood_app_submitted):
    """A submitted application owned by the ICMS admin user."""
    ilb_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    wood_app_submitted.refresh_from_db()

    return wood_app_submitted


def test_manage_checklist_get(ilb_admin_client, wood_application):
    assert not hasattr(wood_application, "checklist")

    manage_checklist = reverse(
        "import:wood:manage-checklist", kwargs={"application_pk": wood_application.pk}
    )
    resp = ilb_admin_client.get(manage_checklist)

    assert resp.status_code == 200

    assert resp.context["page_title"] == "Wood (Quota) Import Licence - Checklist"
    assert resp.context["readonly_view"] is False

    wood_application.refresh_from_db()
    assert hasattr(wood_application, "checklist")


def test_manage_checklist_post(ilb_admin_client, wood_application):
    assert not hasattr(wood_application, "checklist")

    manage_checklist = reverse(
        "import:wood:manage-checklist", kwargs={"application_pk": wood_application.pk}
    )

    resp = ilb_admin_client.post(
        manage_checklist,
        data={
            "import_application": wood_application.pk,
            "case_update": YesNoNAChoices.yes,
            "fir_required": YesNoNAChoices.yes,
            "validity_period_correct": YesNoNAChoices.yes,
            "endorsements_listed": YesNoNAChoices.yes,
            "response_preparation": True,
            "authorisation": True,
            "sigl_wood_application_logged": True,
        },
    )

    assertRedirects(resp, manage_checklist, 302)

    wood_application.refresh_from_db()

    assert hasattr(wood_application, "checklist")
    checklist = wood_application.checklist

    assert checklist.case_update == YesNoNAChoices.yes
    assert checklist.fir_required == YesNoNAChoices.yes
    assert checklist.validity_period_correct == YesNoNAChoices.yes
    assert checklist.endorsements_listed == YesNoNAChoices.yes
    assert checklist.response_preparation is True
    assert checklist.authorisation is True
    assert checklist.sigl_wood_application_logged is True


def test_wood_app_submitted_has_a_licence(wood_app_submitted):
    assert wood_app_submitted.licences.filter(status=ImportApplicationLicence.Status.DRAFT).exists()
