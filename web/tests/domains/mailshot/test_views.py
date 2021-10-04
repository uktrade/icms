from django.utils import timezone

from web.domains.mailshot.models import Mailshot
from web.tests.auth import AuthTestCase

from .factory import MailshotFactory

LOGIN_URL = "/"


class MailshotListViewTest(AuthTestCase):
    url = "/mailshot/"
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
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], "Maintain Mailshots")

    def test_number_of_pages(self):
        MailshotFactory.create_batch(62)

        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        page = response.context_data["page"]
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        MailshotFactory.create_batch(65)
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url + "?page=2")
        page = response.context_data["page"]
        self.assertEqual(len(page.object_list), 15)


class ReceivedMailshotsView(AuthTestCase):
    url = "/mailshot/received/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_case_worker_access(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_exporter_access(self):
        self.login_with_permissions(["exporter_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_importer_access(self):
        self.login_with_permissions(["importer_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["importer_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], "Received Mailshots")


class MailshotCreateViewTest(AuthTestCase):
    url = "/mailshot/new/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access_redirects(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        mailshot = Mailshot.objects.first()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/mailshot/{mailshot.id}/edit/")

    def test_create_as_draft(self):
        self.login_with_permissions(["reference_data_access"])
        self.client.get(self.url)
        mailshot = Mailshot.objects.first()
        self.assertEqual(mailshot.status, Mailshot.Statuses.DRAFT)


class MailshotEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.mailshot = MailshotFactory(status=Mailshot.Statuses.DRAFT)  # Create a mailshot
        self.mailshot.save()
        self.url = f"/mailshot/{self.mailshot.id}/edit/"
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
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_cancel_draft(self):
        self.login_with_permissions(["reference_data_access"])
        self.client.post(self.url, {"action": "cancel"})
        self.mailshot.refresh_from_db()
        self.assertEqual(self.mailshot.status, Mailshot.Statuses.CANCELLED)

    def test_cancel_redirects_to_list(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.post(self.url, {"action": "cancel"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/mailshot/")

    def test_save_draft(self):
        self.login_with_permissions(["reference_data_access"])
        self.client.post(self.url, {"title": "Test", "action": "save_draft"})
        self.mailshot.refresh_from_db()
        self.assertEqual(self.mailshot.title, "Test")

    def test_save_draft_redirects_to_list(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.post(self.url, {"title": "Test", "action": "save_draft"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/mailshot/")

    def test_page_title(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], f"Editing {self.mailshot}")


class MailshotRetractViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.mailshot = MailshotFactory.create(
            status=Mailshot.Statuses.PUBLISHED, published_datetime=timezone.now()
        )
        self.url = f"/mailshot/{self.mailshot.pk}/retract/"
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
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], f"Retract {self.mailshot}")


class MailshotDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()

        self.mailshot = MailshotFactory.create(
            is_to_importers=True,
            is_to_exporters=True,
            status=Mailshot.Statuses.PUBLISHED,
            published_datetime=timezone.now(),
        )

        self.url = f"/mailshot/{self.mailshot.pk}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_mailshot_ilb_admin_access(self):
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data["page_title"], f"Viewing Mailshot ({self.mailshot.pk})"
        )

    def test_exporter_access_forbidden(self):
        self.login_with_permissions(["exporter_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_importer_access_forbidden(self):
        self.login_with_permissions(["importer_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
