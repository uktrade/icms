import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import FirearmsAuthority
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.domains.constabulary.factory import ConstabularyFactory


class TestObsoleteCalibreGroupListView(AuthTestCase):
    url = "/firearms/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Obsolete Calibres"

    def test_page_results(self):
        response = self.ilb_admin_client.get(self.url)
        results = response.context_data["results"]
        assert len(results) == 27


@pytest.mark.django_db
def test_create_firearms_authority(ilb_admin_client, ilb_admin_user, importer, office):
    response = ilb_admin_client.get(f"/importer/{importer.pk}/firearms/create/")
    assert response.status_code == 200

    constabulary = ConstabularyFactory.create(is_active=True)
    data = {
        "certificate_type": FirearmsAuthority.DEACTIVATED_FIREARMS,
        "issuing_constabulary": constabulary.pk,
        "linked_offices": office.pk,
        "reference": "12",
        "postcode": "SW1A 0AA",  # /PS-IGNORE
        "address": "Westminster",
        "start_date": "23-Dec-2020",
        "end_date": "24-Dec-2020",
        "actquantity_set-TOTAL_FORMS": 2,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-0-firearmsact": 1,
        "actquantity_set-0-infinity": "on",
        "actquantity_set-1-firearmsact": 2,
        "actquantity_set-1-quantity": "1",
    }
    response = ilb_admin_client.post(f"/importer/{importer.pk}/firearms/create/", data=data)
    assert response.status_code == 302

    firearms = FirearmsAuthority.objects.get()
    assert office == firearms.linked_offices.first()
    assert response["Location"] == reverse("importer-edit", kwargs={"pk": importer.pk})
