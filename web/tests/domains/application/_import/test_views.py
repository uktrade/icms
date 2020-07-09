from web.tests.auth import AuthTestCase

LOGIN_URL = "/"


class ImportAppplicationCreateViewTest(AuthTestCase):
    url = "/import/apply/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_importer_contact_access(self):
        self.login_with_permissions(["IMP_EDIT_APP"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
