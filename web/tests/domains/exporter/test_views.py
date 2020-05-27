# NOQA: C0301
from django.contrib.auth.models import Permission

from web.domains.exporter.models import Exporter
from web.domains.team.models import Role
from web.tests.auth import AuthTestCase
from web.tests.domains.exporter.factory import ExporterFactory

LOGIN_URL = '/'
PERMISSIONS = ['IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL']


class ExporterListViewTest(AuthTestCase):
    url = '/exporter/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        self.login()
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_admin_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Exporters')

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_number_of_pages(self):
        for i in range(52):
            ExporterFactory()

        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        page = response.context_data['page']
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(53):
            ExporterFactory(is_active=True)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url + '?page=2')
        page = response.context_data['page']
        self.assertEqual(len(page.object_list), 3)


class ExporterEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.exporter = ExporterFactory()
        self.url = f'/exporter/{self.exporter.id}/edit/'
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
                         f"Editing {self.exporter}")


class ExporterCreateViewTest(AuthTestCase):
    url = '/exporter/new/'
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

    def test_exporter_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()
        self.assertEqual(exporter.name, 'test exporter')

    def test_agent_approve_reject_role_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()
        role_name = f'Exporter Contacts:Approve/Reject Agents and Exporters:{exporter.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_agent_approve_reject_role_permissions_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()

        codename = f'IMP_EXPORTER_CONTACTS:AGENT_APPROVER:{exporter.id}:IMP_CERT_AGENT_APPROVER'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:AGENT_APPROVER:{exporter.id}:IMP_CERT_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:AGENT_APPROVER:{exporter.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_edit_role_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()
        role_name = f'Exporter Contacts:Edit Applications:{exporter.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_edit_role_permissions_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()
        codename = f'IMP_EXPORTER_CONTACTS:EDIT_APPLICATION:{exporter.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:EDIT_APPLICATION:{exporter.id}:IMP_CERT_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:EDIT_APPLICATION:{exporter.id}:IMP_CERT_EDIT_APPLICATION'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_view_role_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()
        role_name = f'Exporter Contacts:View Applications/Certificates:{exporter.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_view_role_permissions_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(self.url, {'name': 'test exporter'})
        exporter = Exporter.objects.first()
        codename = f'IMP_EXPORTER_CONTACTS:VIEW_APPLICATION:{exporter.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:VIEW_APPLICATION:{exporter.id}:IMP_CERT_VIEW_APPLICATION'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:VIEW_APPLICATION:{exporter.id}:IMP_CERT_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Create Exporter')
