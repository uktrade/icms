import pytest

from web.domains.case.fir.flows import FurtherInformationRequestFlow
from web.tests.auth import AuthTestCase
from web.tests.domains.case.access import factory as access_factories
from web.tests.domains.case.fir import factory as fir_factories
from web.tests.domains.template.factory import TemplateFactory
from web.tests.viewflow.utils import activation_management_form_data

LOGIN_URL = "/"


def populate_fields(access_request):
    access_request.agent_name = "Agent Smith"
    access_request.agent_address = "50 VS"
    access_request.request_reason = "Import/Export"


@pytest.mark.xfail
class ImporterAccessRequestFIRListViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = access_factories.ImporterAccessRequestProcessFactory()
        # Create an access request task
        access_factories.ImporterAccessRequestTaskFactory(process=self.process, owner=self.user)
        self.fir_process = fir_factories.FurtherInformationRequestProcessFactory(
            parent_process=self.process
        )
        self.url = f"/access/importer/{self.process.pk}/fir/list/"
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

    def test_deleted_firs_not_shown(self):
        # Create a deleted FIR process for importer access request process
        self.second_process = fir_factories.FurtherInformationRequestProcessFactory(
            parent_process=self.process,
            fir=fir_factories.FurtherInformationRequestFactory(is_active=False),
        )
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        response = self.client.get(self.url,)
        fir_list = response.context_data["fir_list"]
        self.assertEqual(len(fir_list), 1)
        self.assertEqual(fir_list.first(), self.fir_process)

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
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        self.client.post(self.url, {"_withdraw": "", "_process_id": self.fir_process.pk})
        respond_task.refresh_from_db()
        self.assertEqual(respond_task.status, "CANCELED")

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
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        self.client.post(self.url, {"_withdraw": "", "_process_id": self.fir_process.pk})
        task = self.fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "send_request")
        self.fir_process.fir.refresh_from_db()
        self.assertEqual(self.fir_process.fir.status, "DRAFT")


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
        self.process = access_factories.ImporterAccessRequestProcessFactory()
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
            {"_save_draft": "", "request_subject": "Testing", "request_detail": "This is a test",},
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
            {"request_subject": "Testing", "request_detail": "This is a test",},
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
            {"request_subject": "Testing", "request_detail": "This is a test",},
            follow=True,  # follow redirect
        )
        # list page context
        fir_process = response.context_data["fir_list"][0]
        task = fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "respond")


@pytest.mark.xfail
class ImporterAccessRequestFIREditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = access_factories.ImporterAccessRequestProcessFactory()
        # Create a send_request task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="DRAFT",
            flow_task=FurtherInformationRequestFlow.send_request,
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
        data = activation_management_form_data()
        data.update(
            {"_save_draft": "", "request_subject": "Testing", "request_detail": " This is a test ",}
        )
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.fir_list_url)

    def test_saves_draft(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update(
            {"_save_draft": "", "request_subject": "Testing", "request_detail": "This is a test",},
        )
        response = self.client.post(self.url, data, follow=True,)  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "DRAFT")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_opens_fir(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update({"request_subject": "Testing", "request_detail": "This is a test",},)
        response = self.client.post(self.url, data, follow=True,)  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "OPEN")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_creates_respond_task(self):
        self.login_with_permissions(["IMP_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update({"request_subject": "Testing", "request_detail": "This is a test",},)
        response = self.client.post(self.url, data, follow=True,)  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        task = fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "respond")


@pytest.mark.xfail
class ImporterAccessRequestFIRResponseViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # create importer access request process
        self.process = access_factories.ImporterAccessRequestProcessFactory()

        # Add test user to importer's team
        # team tasks are restricted to team members with necessary permission
        # TODO: use django-guardian
        # self.process.access_request.linked_importer.members.add(self.user)

        # Create a respond task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="OPEN",
            flow_task=FurtherInformationRequestFlow.respond,
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
        data = activation_management_form_data()
        data.update({"response_detail": "My response is... this!"},)
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/workbasket/")

    @pytest.mark.xfail
    def test_submit_updates_fir_status(self):
        self.login_with_permissions(["IMP_AGENT_APPROVER"])
        data = activation_management_form_data()
        data.update({"response_detail": "This is a test"},)
        self.client.post(self.url, data)
        fir = self.fir_process.fir
        fir.refresh_from_db()
        self.assertEqual(fir.status, "RESPONDED")
        self.assertEqual(fir.response_detail, "This is a test")

    @pytest.mark.xfail
    def test_submit_creates_review_task(self):
        self.login_with_permissions(["IMP_AGENT_APPROVER"])
        data = activation_management_form_data()
        data.update({"response_detail": "This is a test"},)
        self.client.post(self.url, data)
        task = self.fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "review")


@pytest.mark.xfail
class ImporterAccessRequestFIRReviewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # create access request process
        self.process = access_factories.ImporterAccessRequestProcessFactory()

        # Create a review task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="RESPONDED",
            flow_task=FurtherInformationRequestFlow.review,
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
        data = activation_management_form_data()
        self.client.post(self.url, data)
        fir = self.fir_process.fir
        fir.refresh_from_db()
        self.assertEqual(fir.status, "CLOSED")


@pytest.mark.xfail
class ExporterAccessRequestFIRListViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = access_factories.ExporterAccessRequestProcessFactory()
        # Create an access request task
        access_factories.ExporterAccessRequestTaskFactory(process=self.process, owner=self.user)
        self.fir_process = fir_factories.FurtherInformationRequestProcessFactory(
            parent_process=self.process
        )
        self.url = f"/access/exporter/{self.process.pk}/fir/list/"
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_deleted_firs_not_shown(self):
        # Create a deleted FIR process for importer access request process
        self.second_process = fir_factories.FurtherInformationRequestProcessFactory(
            parent_process=self.process,
            fir=fir_factories.FurtherInformationRequestFactory(is_active=False),
        )
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.get(self.url,)
        fir_list = response.context_data["fir_list"]
        self.assertEqual(len(fir_list), 1)
        self.assertEqual(fir_list.first(), self.fir_process)

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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        self.client.post(self.url, {"_withdraw": "", "_process_id": self.fir_process.pk})
        respond_task.refresh_from_db()
        self.assertEqual(respond_task.status, "CANCELED")

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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        self.client.post(self.url, {"_withdraw": "", "_process_id": self.fir_process.pk})
        task = self.fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "send_request")
        self.fir_process.fir.refresh_from_db()
        self.assertEqual(self.fir_process.fir.status, "DRAFT")


@pytest.mark.xfail
class ExporterAccessRequestFIRStartViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        TemplateFactory(
            is_active=True,
            template_code="IAR_RFI_EMAIL",
            template_title="[[REQUEST_REFERENCE]] Further Information Request",
            template_content="""
            Dear [[REQUESTER_NAME]],
            [[REQUEST_REFERENCE]].
            Yours sincerely, [[CURRENT_USER_NAME]]""",
        )
        self.process = access_factories.ExporterAccessRequestProcessFactory()
        self.url = f"/access/exporter/{self.process.pk}/fir/request/"
        self.fir_list_url = f"/access/exporter/{self.process.pk}/fir/list/"
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_save_draft_redirects_to_list(self):
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {"_save_draft": "", "request_subject": "Testing", "request_detail": "This is a test",},
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {"request_subject": "Testing", "request_detail": "This is a test",},
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.post(
            self.url,
            {"request_subject": "Testing", "request_detail": "This is a test",},
            follow=True,  # follow redirect
        )
        # list page context
        fir_process = response.context_data["fir_list"][0]
        task = fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "respond")


@pytest.mark.xfail
class ExporterAccessRequestFIREditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = access_factories.ExporterAccessRequestProcessFactory()
        # Create a send_request task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="DRAFT",
            flow_task=FurtherInformationRequestFlow.send_request,
            owner=self.user,
        )
        self.fir_process = self.task.process
        self.url = f"/fir/{self.fir_process.pk}/send_request/{self.task.pk}/"
        self.fir_list_url = f"/access/exporter/{self.process.pk}/fir/list/"
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_save_draft_redirects_to_list(self):
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update(
            {"_save_draft": "", "request_subject": "Testing", "request_detail": " This is a test ",}
        )
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.fir_list_url)

    def test_saves_draft(self):
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update(
            {"_save_draft": "", "request_subject": "Testing", "request_detail": "This is a test",},
        )
        response = self.client.post(self.url, data, follow=True,)  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "DRAFT")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_opens_fir(self):
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update({"request_subject": "Testing", "request_detail": "This is a test",},)
        response = self.client.post(self.url, data, follow=True,)  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        fir = fir_process.fir
        self.assertEqual(fir.status, "OPEN")
        self.assertEqual(fir.request_detail, "This is a test")
        self.assertEqual(fir.request_subject, "Testing")

    @pytest.mark.xfail
    def test_submit_creates_respond_task(self):
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        data = activation_management_form_data()
        data.update({"request_subject": "Testing", "request_detail": "This is a test",},)
        response = self.client.post(self.url, data, follow=True,)  # follow redirect
        # list page context
        fir_process = response.context_data["fir_list"][0]
        task = fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "respond")


@pytest.mark.xfail
class ExporterAccessRequestFIRResponseViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # create importer access request process
        self.process = access_factories.ExporterAccessRequestProcessFactory()

        # Add test user to exporter's team
        # team tasks are restricted to team members with necessary permission
        # TODO: use django-guardian
        # self.process.access_request.linked_exporter.members.add(self.user)

        # Create a respond task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="OPEN",
            flow_task=FurtherInformationRequestFlow.respond,
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
        self.login_with_permissions(["IMP_CERT_AGENT_APPROVER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @pytest.mark.xfail
    def test_submit_redirects_to_workbasket(self):
        self.login_with_permissions(["IMP_CERT_AGENT_APPROVER"])
        data = activation_management_form_data()
        data.update({"response_detail": "My response is... this!"},)
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/workbasket/")

    @pytest.mark.xfail
    def test_submit_updates_fir_status(self):
        self.login_with_permissions(["IMP_CERT_AGENT_APPROVER"])
        data = activation_management_form_data()
        data.update({"response_detail": "This is a test"},)
        self.client.post(self.url, data)
        fir = self.fir_process.fir
        fir.refresh_from_db()
        self.assertEqual(fir.status, "RESPONDED")
        self.assertEqual(fir.response_detail, "This is a test")

    @pytest.mark.xfail
    def test_submit_creates_review_task(self):
        self.login_with_permissions(["IMP_CERT_AGENT_APPROVER"])
        data = activation_management_form_data()
        data.update({"response_detail": "This is a test"},)
        self.client.post(self.url, data)
        task = self.fir_process.active_tasks().last()
        self.assertEqual(task.flow_task.name, "review")


@pytest.mark.xfail
class ExporterAccessRequestFIRReviewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        # create access request process
        self.process = access_factories.ExporterAccessRequestProcessFactory()

        # Create a review task
        self.task = fir_factories.FurtherInformationRequestTaskFactory(
            process__parent_process=self.process,
            process__fir__status="RESPONDED",
            flow_task=FurtherInformationRequestFlow.review,
            owner=self.user,
        )
        self.fir_process = self.task.process
        self.url = f"/fir/{self.fir_process.pk}/review/{self.task.pk}/"
        self.fir_list_url = f"/access/exporter/{self.process.pk}/fir/list/"
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
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_submit_closes_fir(self):
        self.login_with_permissions(["IMP_CERT_CASE_OFFICER"])
        data = activation_management_form_data()
        self.client.post(self.url, data)
        fir = self.fir_process.fir
        fir.refresh_from_db()
        self.assertEqual(fir.status, "CLOSED")
