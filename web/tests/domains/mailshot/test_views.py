import pytest
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertRedirects

from web.domains.case.services import reference
from web.domains.mailshot.views import MailshotListView
from web.mail.constants import EmailTypes
from web.mail.url_helpers import get_mailshot_detail_view_url
from web.middleware.common import ICMSMiddlewareContext
from web.models import Mailshot, User
from web.sites import SiteName, get_importer_site_domain
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import check_gov_notify_email_was_sent


class TestMailshotListView(AuthTestCase):
    url = "/mailshot/"
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
        assert response.context_data["page_title"] == "Maintain Mailshots"

    def test_number_of_pages(self, importer_one_contact, draft_mailshot):
        objs = [
            Mailshot(title="Mailshot %s" % i, created_by=importer_one_contact) for i in range(62)
        ]
        Mailshot.objects.bulk_create(objs)
        response = self.ilb_admin_client.get(self.url, {"reference": ""})
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self, importer_one_contact):
        objs = [
            Mailshot(title="Mailshot %s" % i, created_by=importer_one_contact) for i in range(65)
        ]
        Mailshot.objects.bulk_create(objs)
        response = self.ilb_admin_client.get(self.url, {"page": "2", "reference": ""})
        page = response.context_data["page"]
        assert len(page.object_list) == 15


class TestReceivedMailshotsView(AuthTestCase):
    url = "/mailshot/received/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_case_worker_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 403

    def test_exporter_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 200

    def test_importer_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.importer_client.get(self.url)
        assert response.context_data["page_title"] == "Received Mailshots"


class TestMailshotCreateView(AuthTestCase):
    url = "/mailshot/new/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access_redirects(self):
        response = self.ilb_admin_client.get(self.url)
        mailshot = Mailshot.objects.first()
        assert response.status_code == 302
        assertRedirects(response, f"/mailshot/{mailshot.id}/edit/")

    def test_create_as_draft(self):
        self.ilb_admin_client.get(self.url)
        mailshot = Mailshot.objects.first()
        assert mailshot.status == Mailshot.Statuses.DRAFT


class TestMailshotEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, draft_mailshot):
        self.mailshot = draft_mailshot
        self.url = f"/mailshot/{self.mailshot.id}/edit/"
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

    def test_save_draft(self):
        self.ilb_admin_client.post(self.url, {"title": "Test", "action": "save_draft"})
        self.mailshot.refresh_from_db()
        assert self.mailshot.title == "Test"

    def test_save_draft_redirects_to_edit(self):
        response = self.ilb_admin_client.post(self.url, {"title": "Test", "action": "save_draft"})
        assert response.status_code == 302
        assertRedirects(
            response, reverse("mailshot-edit", kwargs={"mailshot_pk": self.mailshot.pk})
        )

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == f"Editing {self.mailshot}"


class TestMailshotCancelDraftView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, draft_mailshot):
        self.mailshot = draft_mailshot
        self.url = reverse("mailshot-cancel-draft", kwargs={"mailshot_pk": self.mailshot.id})

    def test_forbidden_access(self):
        response = self.importer_client.post(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == 302

    def test_cancel_draft(self):
        self.ilb_admin_client.post(self.url)
        self.mailshot.refresh_from_db()
        assert self.mailshot.status == Mailshot.Statuses.CANCELLED

    def test_cancel_redirects_to_list(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == 302
        assertRedirects(response, reverse("mailshot-list"))


class TestMailshotPublishDraftView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, draft_mailshot):
        self.mailshot = draft_mailshot
        self.url = reverse("mailshot-publish-draft", kwargs={"mailshot_pk": self.mailshot.id})

    def test_forbidden_access(self):
        response = self.importer_client.post(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == 302

    def test_publish_fails_with_no_document(self):
        response = self.ilb_admin_client.post(self.url, follow=True)
        assert response.status_code == 200

        messages = list(response.context["messages"])
        assert len(messages) == 2
        msg = str(messages[0])
        assert msg == "A document must be uploaded before publishing."

        msg = str(messages[1])
        assert msg == "Please complete form before publishing."

    def test_valid_publish_redirects_to_list(self):
        self.mailshot.documents.create(
            is_active=True,
            filename="dummy",
            content_type="dummy",
            file_size=0,
            path="dummy",
            created_by=self.ilb_admin_user,
        )

        self.mailshot.save()
        self.mailshot.title = "Test"
        self.mailshot.description = "Test Description"
        self.mailshot.email_subject = "Test email subject"
        self.mailshot.email_body = "Test email body"
        self.mailshot.is_to_importers = True
        self.mailshot.is_email = True
        self.mailshot.save()

        response = self.ilb_admin_client.post(self.url)

        assert response.status_code == 302
        assertRedirects(response, reverse("mailshot-list"))

        self.mailshot.refresh_from_db()
        assert self.mailshot.status == Mailshot.Statuses.PUBLISHED
        check_gov_notify_email_was_sent(
            3,
            [
                "I1_A1_main_contact@example.com",  # /PS-IGNORE
                "I1_main_contact@example.com",  # /PS-IGNORE
                "I2_main_contact@example.com",  # /PS-IGNORE
            ],
            EmailTypes.MAILSHOT,
            {
                "icms_url": get_importer_site_domain(),
                "service_name": SiteName.IMPORTER.label,
                "mailshot_url": get_mailshot_detail_view_url(
                    self.mailshot, get_importer_site_domain()
                ),
            },
            exp_subject="Test email subject",
            exp_in_body="Test email body",
        )


class TestMailshotRetractView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, draft_mailshot):
        self.mailshot = draft_mailshot
        self.mailshot.status = Mailshot.Statuses.PUBLISHED
        self.mailshot.published_datetime = timezone.now()
        self.mailshot.reference = "MAIL/42"
        self.mailshot.version = 43
        self.mailshot.save()
        self.url = f"/mailshot/{self.mailshot.pk}/retract/"
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

        assert response.context_data["page_title"] == f"Retract {self.mailshot.get_reference()}"


class TestMailshotDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, draft_mailshot):
        self.mailshot = draft_mailshot
        self.mailshot.is_to_importers = True
        self.mailshot.is_to_exporters = True
        self.mailshot.status = Mailshot.Statuses.PUBLISHED
        self.mailshot.published_datetime = timezone.now()
        self.mailshot.reference = "MAIL/44"
        self.mailshot.version = 45
        self.mailshot.save()
        self.url = f"/mailshot/{self.mailshot.pk}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_mailshot_ilb_admin_access(self):
        response = self.ilb_admin_client.get(self.url)

        assert response.status_code == 200
        assert (
            response.context_data["page_title"]
            == f"Viewing Mailshot ({self.mailshot.get_reference()})"
        )

    def test_exporter_access_forbidden(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_importer_access_forbidden(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403


def test_mailshot_list_queryset(ilb_admin_user):
    st = Mailshot.Statuses
    _create_mailshot(st.DRAFT, ilb_admin_user)
    _create_mailshot(st.PUBLISHED, ilb_admin_user, reference_version=True)
    _create_mailshot(st.RETRACTED, ilb_admin_user, retracted=True, reference_version=True)
    old_version = _create_mailshot(
        st.RETRACTED, ilb_admin_user, retracted=True, reference_version=True
    )
    new_version = _create_mailshot(st.DRAFT, ilb_admin_user)
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


class TestClearMailshotFromWorkbasketView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_user, _setup):
        self.importer_mailshot = _create_mailshot(Mailshot.Statuses.PUBLISHED, ilb_admin_user)
        self.exporter_mailshot = _create_mailshot(
            Mailshot.Statuses.PUBLISHED, ilb_admin_user, is_to_importers=False, is_to_exporters=True
        )

    def test_clear_importer_mailshot(self):
        url = reverse("mailshot-clear", kwargs={"mailshot_pk": self.importer_mailshot.pk})

        for client in [self.exporter_client, self.exporter_agent_client, self.ilb_admin_client]:
            response = client.post(url)
            assert response.status_code == 403

        response = self.importer_client.post(url)
        assert response.status_code == 302

        self.importer_mailshot.refresh_from_db()
        assert self.importer_mailshot.cleared_by.filter(pk=self.importer_user.pk).exists()

    def test_clear_exporter_mailshot(self):
        url = reverse("mailshot-clear", kwargs={"mailshot_pk": self.exporter_mailshot.pk})

        for client in [self.importer_client, self.importer_agent_client, self.ilb_admin_client]:
            response = client.post(url)
            assert response.status_code == 403

        response = self.exporter_client.post(url)
        assert response.status_code == 302

        self.exporter_mailshot.refresh_from_db()
        assert self.exporter_mailshot.cleared_by.filter(pk=self.exporter_user.pk).exists()


def _create_mailshot(
    status: str,
    user: User,
    retracted: bool = False,
    reference_version: bool = False,
    is_to_importers=True,
    is_to_exporters=False,
) -> Mailshot:
    mailshot = Mailshot.objects.create(
        status=status,
        title=f"Title {status}",
        description=f"Description {status}",
        email_subject=f"Email subject {status}",
        email_body=f"Email body {status}",
        is_to_importers=is_to_importers,
        is_to_exporters=is_to_exporters,
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
