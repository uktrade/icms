import pytest
from pytest_django.asserts import assertRedirects

from web.domains.country.models import Country
from web.domains.country.types import CountryGroupName
from web.models import CountryGroup
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL

from .factory import CountryFactory, CountryTranslationSetFactory


@pytest.fixture()
def country_group(db):
    return CountryGroup.objects.get(name=CountryGroupName.EU)


class TestCountryListView(AuthTestCase):
    url = "/country/"
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
        assert response.context_data["page_title"] == "Editing All Countries"

    def test_page_results(self):
        response = self.ilb_admin_client.get(self.url)
        results = response.context_data["object_list"]
        assert len(results) == Country.objects.all().count()


class TestCountryEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.country = CountryFactory(name="Astoria")
        self.url = f"/country/{self.country.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        assert response.context_data["page_title"] == "Editing Astoria"


class TestCountryCreateView(AuthTestCase):
    url = "/country/new/"
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
        assert response.context_data["page_title"] == "Add Country"


class TestCountryGroupDefaultView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = "/country/groups/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        assert response.context_data["page_title"] == "Maintain Country Groups"


class TestCountryGroupView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, country_group):
        self.group = country_group
        self.url = f"/country/groups/{self.group.id}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        assert response.context_data["page_title"] == "Viewing EU - (28 countries)"


class TestCountryGroupEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, country_group):
        self.group = country_group
        self.url = f"/country/groups/{self.group.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def setupCountries(self):
        self.new_country_one = CountryFactory(name="New Country 1", is_active=True)
        self.new_country_two = CountryFactory(name="New Country 2", is_active=True)
        self.new_country_three = CountryFactory(name="New Country 3", is_active=True)
        self.group.countries.set([self.new_country_one, self.new_country_two])

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
        assert response.context_data["page_title"] == "Editing EU - (28 countries)"

    def test_group_countries(self):
        self.setupCountries()
        response = self.ilb_admin_client.get(self.url)
        countries = response.context_data["countries"]
        assert len(countries) == 2
        assert countries[0].name == "New Country 1"
        assert countries[1].name == "New Country 2"

    def test_post_action_anonymous_access(self):
        response = self.anonymous_client.post(self.url, {"action": "add_country"})
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        response = self.importer_client.post(self.url, {"action": "add_country"})
        assert response.status_code == 403

    def test_add_country_page_title(self):
        response = self.ilb_admin_client.post(self.url, {"action": "add_country"})
        assert response.context_data["page_title"] == "Country Search"

    def test_add_country_selected_countries(self):
        self.setupCountries()
        response = self.ilb_admin_client.post(
            self.url,
            {
                "action": "add_country",
                "countries": [self.new_country_one.id, self.new_country_two.id],
            },
        )
        context = response.context_data
        assert len(context["selected_countries"]) == 2
        assert context["selected_countries"][0].name == "New Country 1"
        assert context["selected_countries"][1].name == "New Country 2"

    def test_accept_countries(self):
        self.setupCountries()
        response = self.ilb_admin_client.post(
            self.url,
            {
                "action": "accept_countries",
                "country-selection": [
                    self.new_country_one.id,
                    self.new_country_two.id,
                    self.new_country_three.id,
                ],
            },
        )
        countries = response.context_data["countries"]
        assert len(countries) == 3
        assert countries[0].name == "New Country 1"
        assert countries[1].name == "New Country 2"
        assert countries[2].name == "New Country 3"


class TestCountryTranslationSetListView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.translation_set = CountryTranslationSetFactory(name="Chinese", is_active=True)
        self.translation_set_archived = CountryTranslationSetFactory(
            name="Persian", is_active=False
        )
        self.url = "/country/translations/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        assert response.context_data["page_title"] == "Manage Country Translation Sets"

    def test_post_action_anonymous_access(self):
        response = self.anonymous_client.post(self.url, {"action": "archive"})
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        response = self.importer_client.post(self.url, {"action": "unarchive"})
        assert response.status_code == 403

    def test_archive_translation_set(self):
        self.ilb_admin_client.post(self.url, {"action": "archive", "item": self.translation_set.id})
        self.translation_set.refresh_from_db()
        assert self.translation_set.is_active is False

    def test_unarchive_translation_set(self):
        self.ilb_admin_client.post(
            self.url, {"action": "unarchive", "item": self.translation_set_archived.id}
        )
        self.translation_set_archived.refresh_from_db()
        assert self.translation_set_archived.is_active is True


class TestCountryTranslationSetEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.translation_set = CountryTranslationSetFactory(name="Arabic", is_active=True)
        self.url = f"/country/translations/{self.translation_set.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        assert response.context_data["page_title"] == "Editing Arabic Translation Set"

    def test_post_action_anonymous_access(self):
        response = self.anonymous_client.post(self.url, {"action": "archive"})
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        response = self.importer_client.post(self.url, {"action": "archive"})
        assert response.status_code == 403

    def test_archive_translation_set(self):
        self.ilb_admin_client.post(self.url, {"action": "archive"})
        self.translation_set.refresh_from_db()
        assert self.translation_set.is_active is False


class TestCountryTranslationEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.translation_set = CountryTranslationSetFactory(name="New Country 4", is_active=True)
        self.country = CountryFactory(name="New Country 5", is_active=True)
        self.url = f"/country/translations/{self.translation_set.id}/edit/{self.country.id}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        assert (
            response.context_data["page_title"]
            == "Editing New Country 4 translation of New Country 5"
        )
