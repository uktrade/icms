import datetime

from django.contrib.auth.models import Permission
from django.test import TestCase
from viewflow.models import Process

from web.models import User
from web.tests.domains.user.factory import UserFactory


def grant(user, permission_codename):
    permission = Permission.objects.create(name=permission_codename,
                                           codename=permission_codename,
                                           content_type_id=15)
    user.user_permissions.add(permission)


class ExportAccessRequestFlowTest(TestCase):

    def setUp(self):
        self.test_access_requester = UserFactory(username='test_access_requester',
                                                 password='test',
                                                 password_disposition=User.FULL,
                                                 is_superuser=False,
                                                 is_active=True)
        grant(self.test_access_requester, 'create_access_request')

        self.ilb_admin_user = UserFactory(username='ilb_admin_user',
                                          password='test',
                                          password_disposition=User.FULL,
                                          is_superuser=False,
                                          is_active=True)
        grant(self.ilb_admin_user, 'review_access_request')

    def testFlow(self):
        self.client.force_login(self.test_access_requester)

        response = self.client.post(
            '/access/start/',
            {'request_type': 'MAIN_EXPORTER_ACCESS',
             'organisation_name': 'Test7201',
             'organisation_address': '''50 Victoria St
             London
             SW1H 0TL''',
             '_viewflow_activation-started': datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')}
        )
        assert response.status_code == 302
        process = Process.objects.get()
        self.assertEqual('NEW', process.status)
        self.assertEqual(3, process.task_set.count())

        self.client.logout()
        self.client.force_login(self.ilb_admin_user)

        response = self.client.post(
            '/access/take-ownership/1/'
        )

        assert response.status_code == 302
        process.refresh_from_db()
        self.assertEqual('NEW', process.status)
        self.assertEqual(3, process.task_set.count())

        response = self.client.post(
            '/access/1/review_request/3/',
            {'response': 'APPROVED',
             '_viewflow_activation-started': datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')}
        )
        assert response.status_code == 302

        process.refresh_from_db()
        self.assertEqual('DONE', process.status)
        self.assertEqual(6, process.task_set.count())
