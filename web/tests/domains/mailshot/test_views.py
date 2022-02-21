from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from web.domains.case.services import reference
from web.domains.mailshot.models import Mailshot
from web.domains.mailshot.views import MailshotListView
from web.domains.user.models import User
from web.middleware.common import ICMSMiddlewareContext
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
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], "Maintain Mailshots")

    def test_number_of_pages(self):
        MailshotFactory.create_batch(62)

        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        page = response.context_data["page"]
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        MailshotFactory.create_batch(65)
        self.login_with_permissions(["ilb_admin"])
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
        self.login_with_permissions(["ilb_admin"])
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
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        mailshot = Mailshot.objects.first()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/mailshot/{mailshot.id}/edit/")

    def test_create_as_draft(self):
        self.login_with_permissions(["ilb_admin"])
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
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_cancel_draft(self):
        self.login_with_permissions(["ilb_admin"])
        self.client.post(self.url, {"action": "cancel"})
        self.mailshot.refresh_from_db()
        self.assertEqual(self.mailshot.status, Mailshot.Statuses.CANCELLED)

    def test_cancel_redirects_to_list(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.post(self.url, {"action": "cancel"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/mailshot/")

    def test_save_draft(self):
        self.login_with_permissions(["ilb_admin"])
        self.client.post(self.url, {"title": "Test", "action": "save_draft"})
        self.mailshot.refresh_from_db()
        self.assertEqual(self.mailshot.title, "Test")

    def test_save_draft_redirects_to_edit(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.post(self.url, {"title": "Test", "action": "save_draft"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("mailshot-edit", kwargs={"mailshot_pk": self.mailshot.pk})
        )

    def test_publish_fails_with_no_document(self):
        self.login_with_permissions(["ilb_admin"])

        response = self.client.post(self.url, {"title": "Test", "action": "publish"})
        self.assertEqual(response.status_code, 200)

        mailshot_form = response.context_data["form"]
        self.assertFalse(mailshot_form.is_valid())
        self.assertIn(
            "A document must be uploaded before publishing", mailshot_form.non_field_errors()
        )

    def test_valid_publish_redirects_to_list(self):
        self.login_with_permissions(["ilb_admin"])

        self.mailshot.documents.create(
            is_active=True,
            filename="dummy",
            content_type="dummy",
            file_size=0,
            path="dummy",
            created_by=self.user,
        )
        self.mailshot.save()

        response = self.client.post(
            self.url,
            {
                "action": "publish",
                "title": "Test",
                "description": "Test Description",
                "email_subject": "Test email subject",
                "email_body": "Test email body",
                "recipients": "importers",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/mailshot/")

        self.mailshot.refresh_from_db()
        self.assertEqual(self.mailshot.status, Mailshot.Statuses.PUBLISHED)

    def test_page_title(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], f"Editing {self.mailshot}")


class MailshotRetractViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.mailshot = MailshotFactory.create(
            status=Mailshot.Statuses.PUBLISHED,
            published_datetime=timezone.now(),
            reference="MAIL/42",
            version=43,
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
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(
            response.context_data["page_title"], f"Retract {self.mailshot.get_reference()}"
        )


class MailshotDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()

        self.mailshot = MailshotFactory.create(
            is_to_importers=True,
            is_to_exporters=True,
            status=Mailshot.Statuses.PUBLISHED,
            published_datetime=timezone.now(),
            reference="MAIL/44",
            version=45,
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
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context_data["page_title"],
            f"Viewing Mailshot ({self.mailshot.get_reference()})",
        )

    def test_exporter_access_forbidden(self):
        self.login_with_permissions(["exporter_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_importer_access_forbidden(self):
        self.login_with_permissions(["importer_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


def test_mailshot_list_queryset(test_icms_admin_user):
    st = Mailshot.Statuses
    _create_mailshot(st.DRAFT, test_icms_admin_user)
    _create_mailshot(st.PUBLISHED, test_icms_admin_user, reference_version=True)
    _create_mailshot(st.RETRACTED, test_icms_admin_user, retracted=True, reference_version=True)
    old_version = _create_mailshot(
        st.RETRACTED, test_icms_admin_user, retracted=True, reference_version=True
    )
    new_version = _create_mailshot(st.DRAFT, test_icms_admin_user)
    new_version.reference = old_version.reference
    new_version.version = old_version.version + 1
    new_version.save()

    v = MailshotListView()
    new_version, old_version, retracted, published, draft = v.get_queryset()

    assert new_version.get_reference() == "MAIL/3 (Version 2)"
    assert old_version.get_reference() == "MAIL/3 (Version 1)"
    assert retracted.get_reference() == "MAIL/2 (Version 1)"
    assert published.get_reference() == "MAIL/1 (Version 1)"
    assert draft.get_reference() == "Not Yet Assigned"

    assert new_version.last_version_for_ref == 2
    assert old_version.last_version_for_ref == 2
    assert retracted.last_version_for_ref == 1
    assert published.last_version_for_ref == 1
    assert draft.last_version_for_ref is None


def _create_mailshot(
    status: str, user: User, retracted: bool = False, reference_version: bool = False
) -> Mailshot:
    mailshot = Mailshot.objects.create(
        status=status,
        title=f"Title {status}",
        description=f"Description {status}",
        email_subject=f"Email subject {status}",
        email_body=f"Email body {status}",
        is_to_importers=True,
        is_to_exporters=False,
        published_by=user,
        published_datetime=timezone.now(),
        created_by=user,
    )

    if retracted:
        mailshot.is_retraction_email = True
        mailshot.retract_email_subject = "Retract email"
        mailshot.retract_email_body = "Retract body"
        mailshot.retracted_by = user
        mailshot.retracted_datetime = timezone.now()
        mailshot.save()

    if reference_version:
        icms = ICMSMiddlewareContext()
        mailshot.reference = reference.get_mailshot_reference(icms.lock_manager)
        mailshot.version = F("version") + 1
        mailshot.save()

    return mailshot
