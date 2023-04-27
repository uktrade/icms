import re

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import Country, TextilesApplication


def _get_view_url(view_name, kwargs=None):
    return reverse(f"import:textiles:{view_name}", kwargs=kwargs)


@pytest.fixture
def textiles_app_pk(importer_client, importer_one_main_contact, office, importer):
    "Creates a textiles application to be used in tests, also tests the create-textiles endpoint"

    url = reverse("import:create-textiles")
    post_data = {"importer": importer.pk, "importer_office": office.pk}

    count_before = TextilesApplication.objects.all().count()

    resp = importer_client.post(url, post_data)

    assert TextilesApplication.objects.all().count() == count_before + 1

    application_pk = re.search(r"\d+", resp.url).group(0)

    expected_url = _get_view_url("edit", {"application_pk": application_pk})
    assertRedirects(resp, expected_url, 302)

    return application_pk


def test_textiles_app_edit(importer_client, textiles_app_pk, test_import_user):
    _add_goods_to_app(importer_client, textiles_app_pk, test_import_user)
    textiles_app = TextilesApplication.objects.get(pk=textiles_app_pk)

    assert textiles_app.applicant_reference == "New textiles"
    assert textiles_app.goods_description == "A lot of textiles"


def _add_goods_to_app(importer_client, textiles_app_pk, test_import_user):
    url = _get_view_url("edit", kwargs={"application_pk": textiles_app_pk})
    belarus = Country.objects.get(name="Belarus")
    ghana = Country.objects.get(name="Ghana")

    form_data = {
        "contact": test_import_user.pk,
        "applicant_reference": "New textiles",
        "goods_cleared": True,
        "shipping_year": 2021,
        "origin_country": belarus.pk,
        "consignment_country": ghana.pk,
        "category_commodity_group": 122,
        "commodity": 1634,
        "goods_description": "A lot of textiles",
        "quantity": 5,
    }

    response = importer_client.post(url, data=form_data)

    assert response.status_code == 302

    return response


def test_textiles_app_edit_invalid_form_data(importer_client, textiles_app_pk):
    url = _get_view_url("edit", kwargs={"application_pk": textiles_app_pk})
    response = importer_client.post(url, data={"shipping_year": "invalid form data"})

    assert response.status_code == 200
