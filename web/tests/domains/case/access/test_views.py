import pytest
from django.test import Client

from web.domains.case.fir.models import FurtherInformationRequest
from web.tests.auth import AuthTestCase
from web.tests.domains.case.access import factories as access_factories
from web.tests.domains.case.fir import factory as fir_factories
from web.tests.domains.template.factory import TemplateFactory
from web.tests.domains.user.factory import ActiveUserFactory
from web.tests.flow import factories as process_factories

LOGIN_URL = "/"


class AccessRequestTestBase(AuthTestCase):
    def setUp(self):
        super().setUp()

        # TODO: figure out how to parametrize across importer/exporter
        if True:
            self.process = access_factories.ImporterAccessRequestFactory()
        else:
            self.process = access_factories.ExporterAccessRequestFactory()

        process_factories.TaskFactory.create(process=self.process, task_type="process")
        self.fir_process = fir_factories.FurtherInformationRequestFactory()
        self.process.further_information_requests.add(self.fir_process)

        # TODO: different tests might need different url
        self.url = f"/case/access/{self.process.pk}/firs/list/"

        self.redirect_url = f"{LOGIN_URL}?next={self.url}"


# TODO: figure out how to parametrize across importer/exporter
class ImporterAccessRequestFIRListViewTest(AccessRequestTestBase):
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

    def test_deleted_firs_not_shown(self):
        self.second_fir = fir_factories.FurtherInformationRequestFactory(
            is_active=False, status=FurtherInformationRequest.DELETED
        )
        self.process.further_information_requests.add(self.second_fir)
        self.login_with_permissions(["reference_data_access"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        fir_list = response.context["firs"]
        self.assertEqual(len(fir_list), 1)
        self.assertEqual(fir_list.first(), self.fir_process)

    @pytest.mark.xfail
    def test_withdraw_cancels_respond_task(self):
        # Create a respond_task and a start_task as it's previous task .
        # FIR flow starter user is also the owner of send_request and review tasks.
        # Hence start task is needed and will always exist in a normal flow.

        # start task
        start_task = fir_factories.FurtherInformationRequestTaskFactory(
            process=self.fir_process,
            flow_task=self.fir_process.flow_class.start,
            owner=self.user,
            status="DONE",
        )
        # respond task
        respond_task = fir_factories.FurtherInformationRequestTaskFactory(
            process=self.fir_process,
            flow_task=self.fir_process.flow_class.respond,
            owner=start_task.owner,
        )
        self.login_with_permissions(["reference_data_access"])
        self.client.post(self.url, {"_withdraw": "", "_process_id": self.fir_process.pk})
        respond_task.refresh_from_db()
        self.assertEqual(respond_task.status, "CANCELED")

    @pytest.mark.xfail
    def test_withdraw_creates_draft_fir(self):
        # start task
        start_task = fir_factories.FurtherInformationRequestTaskFactory(
            process=self.fir_process,
            flow_task=self.fir_process.flow_class.start,
            owner=self.user,
            status="DONE",
        )
        fir_factories.FurtherInformationRequestTaskFactory(
            process=self.fir_process,
            flow_task=self.fir_process.flow_class.respond,
            owner=start_task.owner,
        )
        task = fir_factories.FurtherInformationRequestTaskFactory(
            process=self.fir_process, flow_task=self.fir_process.flow_class.respond
        )
        self.login_with_permissions(["reference_data_access"])
        self.client.post(self.url, {"_withdraw": "", "_process_id": self.fir_process.pk})
        task = self.fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "send_request")
        self.fir_process.fir.refresh_from_db()
        self.assertEqual(self.fir_process.fir.status, "DRAFT")


# TODO: figure out how to parametrize across importer/exporter
@pytest.mark.xfail
class ImporterAccessRequestFIRStartViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # TODO: Create templates fixture and load it in tests?
        # Template required for creating an fir
        TemplateFactory(
            is_active=True,
            template_code="IAR_RFI_EMAIL",
            template_title="[[REQUEST_REFERENCE]] Further Information Request",
            template_content="""
            Dear [[REQUESTER_NAME]],
            [[REQUEST_REFERENCE]].
            Yours sincerely, [[CURRENT_USER_NAME]]""",
        )
        self.process = access_factories.ImporterAccessRequestFactory()
        self.url = f"/access/importer/{self.process.pk}/fir/request/"
        self.fir_list_url = f"/access/importer/{self.process.pk}/fir/list/"
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
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_save_draft_redirects_to_list(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {
                "_save_draft": "",
                "request_subject": "Testing",
                "request_detail": """
                    This is a test
                """,
            },
        )
        self.assertRedirects(response, self.fir_list_url)

    def test_saves_draft(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {
                "_save_draft": "",
                "request_subject": "Testing",
                "request_detail": "This is a test",
            },
            follow=True,  # follow redirect
        )
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "DRAFT")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_opens_fir(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {
                "request_subject": "Testing",
                "request_detail": "This is a test",
            },
            follow=True,  # follow redirect
        )
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "OPEN")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_creates_respond_task(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {
                "request_subject": "Testing",
                "request_detail": "This is a test",
            },
            follow=True,  # follow redirect
        )
        # list page context
        fir_process = response.context_data["fir_list"][0]
        task = fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "respond")


# TODO: figure out how to parametrize across importer/exporter
@pytest.mark.xfail
class ImporterAccessRequestFIREditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = access_factories.ImporterAccessRequestFactory()
        # Create a send_request task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="DRAFT",
            owner=self.user,
        )
        self.fir_process = self.task.process
        self.url = f"/fir/{self.fir_process.pk}/send_request/{self.task.pk}/"
        self.fir_list_url = f"/access/importer/{self.process.pk}/fir/list/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @pytest.mark.xfail
    def test_authorized_access(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_save_draft_redirects_to_list(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = {
            "_save_draft": "",
            "request_subject": "Testing",
            "request_detail": " This is a test ",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.fir_list_url)

    def test_saves_draft(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = {
            "_save_draft": "",
            "request_subject": "Testing",
            "request_detail": "This is a test",
        }
        response = self.client.post(
            self.url,
            data,
            follow=True,
        )  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "DRAFT")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_opens_fir(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = {
            "request_subject": "Testing",
            "request_detail": "This is a test",
        }
        response = self.client.post(
            self.url,
            data,
            follow=True,
        )  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "OPEN")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_creates_respond_task(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = {
            "request_subject": "Testing",
            "request_detail": "This is a test",
        }
        response = self.client.post(
            self.url,
            data,
            follow=True,
        )  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        task = fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "respond")


# TODO: figure out how to parametrize across importer/exporter
@pytest.mark.xfail
class ImporterAccessRequestFIRResponseViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # create importer access request process
        self.process = access_factories.ImporterAccessRequestFactory()

        # Add test user to importer's team
        # team tasks are restricted to team members with necessary permission
        # TODO: use django-guardian
        # self.process.access_request.linked_importer.members.add(self.user)

        # Create a respond task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="OPEN",
            owner=self.user,
        )
        self.fir_process = self.task.process
        self.url = f"/fir/{self.fir_process.pk}/respond/{self.task.pk}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @pytest.mark.xfail
    def test_authorized_access(self):
        self.login_with_permissions(["IMP_AGENT_APPROVER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @pytest.mark.xfail
    def test_submit_redirects_to_workbasket(self):
        self.login_with_permissions(["IMP_AGENT_APPROVER"])
        data = {"response_detail": "My response is... this!"}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/workbasket/")

    @pytest.mark.xfail
    def test_submit_updates_fir_status(self):
        self.login_with_permissions(["IMP_AGENT_APPROVER"])
        data = {"response_detail": "This is a test"}
        self.client.post(self.url, data)
        fir = self.fir_process.fir
        fir.refresh_from_db()
        self.assertEqual(fir.status, "RESPONDED")
        self.assertEqual(fir.response_detail, "This is a test")

    @pytest.mark.xfail
    def test_submit_creates_review_task(self):
        self.login_with_permissions(["IMP_AGENT_APPROVER"])
        data = {"response_detail": "This is a test"}
        self.client.post(self.url, data)
        task = self.fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "review")


# TODO: figure out how to parametrize across importer/exporter
@pytest.mark.xfail
class ImporterAccessRequestFIRReviewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # create access request process
        self.process = access_factories.ImporterAccessRequestFactory()

        # Create a review task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="RESPONDED",
            owner=self.user,
        )
        self.fir_process = self.task.process
        self.url = f"/fir/{self.fir_process.pk}/review/{self.task.pk}/"
        self.fir_list_url = f"/access/importer/{self.process.pk}/fir/list/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @pytest.mark.xfail
    def test_authorized_access(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_submit_closes_fir(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        self.client.post(self.url, {})
        fir = self.fir_process.fir
        fir.refresh_from_db()
        self.assertEqual(fir.status, "CLOSED")


@pytest.mark.django_db
def test_list_importer_access_request_ok():
    client = Client()

    user = ActiveUserFactory.create()
    client.login(username=user.username, password="test")
    response = client.get("/access/importer/")

    assert response.status_code == 403

    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    access_factories.ImporterAccessRequestFactory.create()
    client.login(username=ilb_admin.username, password="test")
    response = client.get("/access/importer/")

    assert response.status_code == 200
    assert "Search Importer Access Requests" in response.content.decode()


@pytest.mark.django_db
def test_list_exporter_access_request_ok():
    client = Client()

    user = ActiveUserFactory.create()
    client.login(username=user.username, password="test")
    response = client.get("/access/exporter/")

    assert response.status_code == 403

    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    access_factories.ExporterAccessRequestFactory.create()
    client.login(username=ilb_admin.username, password="test")
    response = client.get("/access/exporter/")

    assert response.status_code == 200
    assert "Search Exporter Access Requests" in response.content.decode()
