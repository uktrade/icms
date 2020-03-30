from web.tests.auth import AuthTestCase

from .factory import MailshotFactory

LOGIN_URL = '/'


class MailshotListViewTest(AuthTestCase):
    url = '/mailshots/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_authorized_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Mailshots')

    def test_number_of_pages(self):
        # Create 51 product legislation as paging lists 50 items per page
        for i in range(62):
            MailshotFactory()

        self.login()
        response = self.client.get(self.url)
        page = response.context_data['page']
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(65):
            MailshotFactory()
        self.login()
        response = self.client.get(self.url + '?page=2')
        page = response.context_data['page']
        self.assertEqual(len(page.object_list), 15)

