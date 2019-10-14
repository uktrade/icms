from web.tests.auth import AuthTestCase

from .factory import ProductLegislationFactory

LOGIN_URL = '/'
PERMISSIONS = ['IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL']


class ProductLegislationListViewTest(AuthTestCase):
    url = '/product-legislation/'
    redirect_url = f'{LOGIN_URL}?next={url}'

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
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Product Legislation')

    def test_number_of_pages(self):
        # Create 51 product legislation as paging lists 50 items per page
        for i in range(51):
            ProductLegislationFactory()

        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        page = response.context_data['page']
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(51):
            ProductLegislationFactory()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url + '?page=2')
        page = response.context_data['page']
        self.assertEqual(len(page.object_list), 1)


class ProductLegislationCreateViewTest(AuthTestCase):
    url = '/product-legislation/new/'
    redirect_url = f'{LOGIN_URL}?next={url}'

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
        self.assertEqual(response.context_data['page_title'],
                         'New Product Legislation')

    def test_create_message(self):
        self.login


class ProductLegislationUpdateViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.legislation = ProductLegislationFactory(
        )  # Create a product legislation
        self.url = f'/product-legislation/{self.legislation.id}/edit/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

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
        self.assertEqual(response.context_data['page_title'],
                         f"Editing {self.legislation}")


class ProductLegislationDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.legislation = ProductLegislationFactory()
        self.url = f'/product-legislation/{self.legislation.id}/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

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
        self.assertEqual(response.context_data['page_title'],
                         f"Viewing {self.legislation}")
