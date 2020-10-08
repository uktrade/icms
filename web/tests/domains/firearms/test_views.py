from web.tests.auth import AuthTestCase

from .factory import ObsoleteCalibreGroupFactory

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
