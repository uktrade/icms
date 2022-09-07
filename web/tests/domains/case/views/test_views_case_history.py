from pytest_django.asserts import assertTemplateUsed

from web.tests.helpers import CaseURLS


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
