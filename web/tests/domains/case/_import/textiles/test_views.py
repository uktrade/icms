import re

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.domains.case._import.textiles.models import TextilesApplication


def _get_view_url(view_name, kwargs=None):
    return reverse(f"import:textiles:{view_name}", kwargs=kwargs)


@pytest.fixture(autouse=True)
def log_in_test_user(client, test_import_user):
    "Logs in the test_import_user for all tests."

    assert (
        client.login(username=test_import_user.username, password="test") is True
    ), "Failed to login"


@pytest.fixture
def textiles_app_pk(client, office, importer):
    "Creates a textiles application to be used in tests, also tests the create-textiles endpoint"

    url = reverse("import:create-textiles")
    post_data = {"importer": importer.pk, "importer_office": office.pk}

    count_before = TextilesApplication.objects.all().count()

    resp = client.post(url, post_data)

    assert TextilesApplication.objects.all().count() == count_before + 1

    application_pk = re.search(r"\d+", resp.url).group(0)

    expected_url = _get_view_url("edit", {"application_pk": application_pk})
    assertRedirects(resp, expected_url, 302)

    return application_pk


def _add_goods_to_app(client, textiles_app_pk, test_import_user):
    url = _get_view_url("edit", kwargs={"application_pk": textiles_app_pk})

    form_data = {
        "contact": test_import_user.pk,
        "applicant_reference": "New textiles",
        "goods_cleared": True,
        "shipping_year": 2021,
        "origin_country": 16,
        "consignment_country": 54,
        "category_commodity_group": 122,
        "commodity": 1634,
        "goods_description": "A lot of textiles",
        "quantity": 5,
    }

    response = client.post(url, data=form_data)

    assert response.status_code == 302

    return response


def test_textiles_app_edit(client, textiles_app_pk, test_import_user):
    _add_goods_to_app(client, textiles_app_pk, test_import_user)
    textiles_app = TextilesApplication.objects.get(pk=textiles_app_pk)

    assert textiles_app.applicant_reference == "New textiles"
    assert textiles_app.goods_description == "A lot of textiles"


def test_textiles_app_edit_invalid_form_data(client, textiles_app_pk):
    url = _get_view_url("edit", kwargs={"application_pk": textiles_app_pk})
    response = client.post(url, data={})

    assert response.status_code == 200
