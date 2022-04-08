import datetime

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from web.domains.case._import.fa_sil.models import SILChecklist
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import set_application_licence_or_certificate_active
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS


@pytest.fixture
def completed_app(fa_sil_app_submitted, icms_admin_client):
    """A completed firearms sil application."""
    app = fa_sil_app_submitted

    icms_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Now start authorisation
    response = icms_admin_client.post(CaseURLS.authorise_application(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()
    set_application_licence_or_certificate_active(app)

    return app


def test_can_get_history(completed_app, icms_admin_client, importer_client, exporter_client):
    # Test can access the history of an application
    url = CaseURLS.get_application_history(completed_app.pk, "import")

    response = icms_admin_client.get(url)
    assert response.status_code == 200
    _check_response_context(completed_app, response.context)

    assertTemplateUsed(response, "web/domains/case/import_licence_history.html")

    response = importer_client.get(url)
    assert response.status_code == 200
    _check_response_context(completed_app, response.context)

    assertTemplateUsed(response, "web/domains/case/import_licence_history.html")

    response = exporter_client.get(url)
    assert response.status_code == 403


def _check_response_context(app, context):
    licences = context["licences"]
    assert len(licences) == 1

    licence_docs = licences[0]["documents"]
    assert len(licence_docs) == 2
    assert ["Cover Letter", "Licence"] == sorted(d["name"] for d in licence_docs)


def _set_valid_licence(app):
    licence = app.get_most_recent_licence()
    licence.case_completion_date = datetime.date(2020, 1, 1)
    licence.licence_start_date = datetime.date(2020, 6, 1)
    licence.licence_end_date = datetime.date(2024, 12, 31)
    licence.issue_paper_licence_only = False
    licence.save()


def _add_valid_checklist(app):
    app.checklist = SILChecklist.objects.create(
        import_application=app,
        case_update=YesNoNAChoices.yes,
        fir_required=YesNoNAChoices.yes,
        response_preparation=True,
        validity_period_correct=YesNoNAChoices.yes,
        endorsements_listed=YesNoNAChoices.yes,
        authorisation=True,
        authority_required=YesNoNAChoices.yes,
        authority_received=YesNoNAChoices.yes,
        authority_cover_items_listed=YesNoNAChoices.yes,
        quantities_within_authority_restrictions=YesNoNAChoices.yes,
        authority_police=YesNoNAChoices.yes,
    )
