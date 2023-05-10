import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import ImportApplicationLicence
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS


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
