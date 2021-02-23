from web.tests.auth import AuthTestCase

from .factory import CountryFactory, CountryGroupFactory, CountryTranslationSetFactory

LOGIN_URL = "/"
PERMISSIONS = ["reference_data_access"]


class CountryListViewTest(AuthTestCase):
    url = "/country/"
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
        self.assertEqual(response.context_data["page_title"], "Editing All Countries")

    def test_page_results(self):
        for i in range(3):
            CountryFactory()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        results = response.context_data["object_list"]
        self.assertEqual(len(results), 183)


class CountryEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory(name="Astoria")
        self.url = f"/country/{self.country.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        self.assertEqual(response.context_data["page_title"], "Editing Astoria")


class CountryCreateViewTest(AuthTestCase):
    url = "/country/new/"
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
        self.assertEqual(response.context_data["page_title"], "New Country")


class CountryGroupDefaultViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        CountryGroupFactory(name="Asian Countries")
        CountryGroupFactory(name="American Countries")
        self.url = "/country/groups/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        self.assertEqual(
            response.context_data["page_title"], "Viewing American Countries - (0 countries)"
        )


class CountryGroupViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.group = CountryGroupFactory(name="European Countries")
        self.url = f"/country/groups/{self.group.id}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        self.assertEqual(
            response.context_data["page_title"], "Viewing European Countries - (0 countries)"
        )


class CountryGroupEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.group = CountryGroupFactory(name="African Countries")
        self.url = f"/country/groups/{self.group.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def setupCountries(self):
        self.new_country_one = CountryFactory(name="New Country 1", is_active=True)
        self.new_country_two = CountryFactory(name="New Country 2", is_active=True)
        self.new_country_three = CountryFactory(name="New Country 3", is_active=True)
        self.group.countries.set([self.new_country_one, self.new_country_two])

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
        self.assertEqual(
            response.context_data["page_title"], "Editing African Countries - (0 countries)"
        )

    def test_group_countries(self):
        self.setupCountries()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        countries = response.context_data["countries"]
        self.assertEqual(len(countries), 2)
        self.assertEqual(countries[0].name, "New Country 1")
        self.assertEqual(countries[1].name, "New Country 2")

    def test_post_action_anonymous_access(self):
        response = self.client.post(self.url, {"action": "add_country"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        self.login()
        response = self.client.post(self.url, {"action": "add_country"})
        self.assertEqual(response.status_code, 403)

    def test_add_country_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {"action": "add_country"})
        self.assertEqual(response.context_data["page_title"], "Country Search")

    def test_add_country_selected_countries(self):
        self.setupCountries()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(
            self.url,
            {
                "action": "add_country",
                "countries": [self.new_country_one.id, self.new_country_two.id],
            },
        )
        context = response.context_data
        self.assertEqual(len(context["selected_countries"]), 2)
        self.assertEqual(context["selected_countries"][0].name, "New Country 1")
        self.assertEqual(context["selected_countries"][1].name, "New Country 2")

    def test_accept_countries(self):
        self.setupCountries()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(
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
        self.assertEqual(len(countries), 3)
        self.assertEqual(countries[0].name, "New Country 1")
        self.assertEqual(countries[1].name, "New Country 2")
        self.assertEqual(countries[2].name, "New Country 3")


class CountryTranslationSetListViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.translation_set = CountryTranslationSetFactory(name="Chinese", is_active=True)
        self.translation_set_archived = CountryTranslationSetFactory(
            name="Persian", is_active=False
        )
        self.url = "/country/translations/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        self.assertEqual(response.context_data["page_title"], "Manage Country Translation Sets")

    def test_post_action_anonymous_access(self):
        response = self.client.post(self.url, {"action": "archive"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        self.login()
        response = self.client.post(self.url, {"action": "unarchive"})
        self.assertEqual(response.status_code, 403)

    def test_archive_translation_set(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {"action": "archive", "item": self.translation_set.id})
        self.translation_set.refresh_from_db()
        self.assertFalse(self.translation_set.is_active)

    def test_unarchive_translation_set(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(
            self.url, {"action": "unarchive", "item": self.translation_set_archived.id}
        )
        self.translation_set_archived.refresh_from_db()
        self.assertTrue(self.translation_set_archived.is_active)


class CountryTranslationSetEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.translation_set = CountryTranslationSetFactory(name="Arabic", is_active=True)
        self.url = f"/country/translations/{self.translation_set.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        self.assertEqual(response.context_data["page_title"], "Editing Arabic Translation Set")

    def test_post_action_anonymous_access(self):
        response = self.client.post(self.url, {"action": "archive"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        self.login()
        response = self.client.post(self.url, {"action": "archive"})
        self.assertEqual(response.status_code, 403)

    def test_archive_translation_set(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {"action": "archive"})
        self.translation_set.refresh_from_db()
        self.assertFalse(self.translation_set.is_active)


class CountryTranslationEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.translation_set = CountryTranslationSetFactory(name="New Country 4", is_active=True)
        self.country = CountryFactory(name="New Country 5", is_active=True)
        self.url = f"/country/translations/{self.translation_set.id}/edit/{self.country.id}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
        self.assertEqual(
            response.context_data["page_title"],
            "Editing New Country 4 translation of New Country 5",
        )
