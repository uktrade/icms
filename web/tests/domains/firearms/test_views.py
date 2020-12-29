import pytest
from django.test.client import Client

from web.domains.firearms.models import FirearmsAuthority
from web.domains.user.models import User
from web.tests.auth import AuthTestCase
from web.tests.domains.constabulary.factory import ConstabularyFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.domains.user.factory import UserFactory

from .factory import FirearmsActFactory, ObsoleteCalibreGroupFactory

LOGIN_URL = "/"
PERMISSIONS = ["reference_data_access"]


class ObsoleteCalibreGroupListView(AuthTestCase):
    url = "/firearms/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], "Maintain Obsolete Calibres")

    def test_page_results(self):
        for i in range(58):
            ObsoleteCalibreGroupFactory(is_active=True)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        results = response.context_data["results"]
        self.assertEqual(len(results), 58)


@pytest.mark.django_db
def test_create_firearms_authority():
    ilb_admin = UserFactory.create(
        is_active=True,
        account_status=User.ACTIVE,
        password_disposition=User.FULL,
        permission_codenames=["reference_data_access"],
    )
    office_one, office_two = OfficeFactory.create_batch(2, is_active=True)
    importer = ImporterFactory.create(is_active=True, offices=[office_one, office_two])

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/importer/{importer.pk}/firearms-authorities/create/")
    assert response.status_code == 200

    constabulary = ConstabularyFactory.create(is_active=True)
    firearms_act_one, firearms_act_two = FirearmsActFactory.create_batch(2, created_by=ilb_admin)
    data = {
        "certificate_type": FirearmsAuthority.DEACTIVATED_FIREARMS,
        "issuing_constabulary": constabulary.pk,
        "linked_offices": office_one.pk,
        "reference": "12",
        "postcode": "SW1A 0AA",
        "address": "Westminster",
        "start_date": "23-Dec-2020",
        "end_date": "24-Dec-2020",
        "actquantity_set-TOTAL_FORMS": 2,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-0-firearmsact": firearms_act_one.pk,
        "actquantity_set-0-infinity": "on",
        "actquantity_set-1-firearmsact": firearms_act_two.pk,
        "actquantity_set-1-quantity": "1",
    }
    response = client.post(f"/importer/{importer.pk}/firearms-authorities/create/", data=data)
    assert response.status_code == 302

    firearms_authority = FirearmsAuthority.objects.get()
    assert office_one == firearms_authority.linked_offices.first()
    assert (
        response["Location"]
        == f"/importer/{importer.pk}/firearms-authorities/{firearms_authority.pk}/edit/"
    )
