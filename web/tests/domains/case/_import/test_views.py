import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertRedirects

from web.domains.case._import.models import LiteHMRCChiefRequest
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.models import VariationRequest
from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.importer.models import Importer
from web.flow.models import Task
from web.tests.domains.importer import factory as importer_factories
from web.tests.domains.office import factory as office_factories
from web.tests.domains.user import factory as user_factories
from web.tests.flow import factories as process_factories

from . import factory


@pytest.mark.django_db
def test_preview_cover_letter():
    ilb_admin = user_factories.ActiveUserFactory.create(permission_codenames=["ilb_admin"])
    user = user_factories.ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = importer_factories.ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    process_factories.TaskFactory.create(process=process, task_type=Task.TaskType.PROCESS)
    oil_app = process.get_specific_model()
    oil_app.licences.create()

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    url = reverse(
        "case:preview-cover-letter", kwargs={"application_pk": process.pk, "case_type": "import"}
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=CoverLetter.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 19000 < len(pdf) < 30000


@pytest.mark.django_db
def test_preview_licence():
    ilb_admin = user_factories.ActiveUserFactory.create(permission_codenames=["ilb_admin"])
    user = user_factories.ActiveUserFactory.create(permission_codenames=["importer_access"])
    office = office_factories.OfficeFactory.create(
        address_1="22 Some Avenue",
        address_2="Some Way",
        address_3="Some Town",
        postcode="S93bl",  # /PS-IGNORE
    )
    importer = importer_factories.ImporterFactory.create(
        type=Importer.ORGANISATION, user=user, eori_number="GB123456789", name="Importer Name"
    )

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        importer_office=office,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    process_factories.TaskFactory.create(process=process, task_type=Task.TaskType.PROCESS)
    oil_app = process.get_specific_model()
    oil_app.licences.create()

    client = Client()
    client.login(username=ilb_admin.username, password="test")

    url = reverse(
        "case:licence-preview", kwargs={"application_pk": process.pk, "case_type": "import"}
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence-Preview.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 19000 < len(pdf) < 30000


class TestBypassChiefView:
    client: "Client"
    wood_app: WoodQuotaApplication

    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, wood_app_submitted):
        """using the submitted app override the app to the state we want."""
        wood_app_submitted.status = ImpExpStatus.PROCESSING
        wood_app_submitted.save()

        task = wood_app_submitted.tasks.get(is_active=True)
        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(
            process=wood_app_submitted, task_type=Task.TaskType.CHIEF_WAIT, previous=task
        )

        self.wood_app = wood_app_submitted
        LiteHMRCChiefRequest.objects.create(
            import_application=self.wood_app,
            case_reference=self.wood_app.reference,
            request_data={"foo": "bar"},
            request_sent_datetime=timezone.now(),
        )

    def test_bypass_chief_success(self):
        url = reverse(
            "import:bypass-chief",
            kwargs={"application_pk": self.wood_app.pk, "chief_status": "success"},
        )
        resp = self.client.post(url)

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.COMPLETED])
        assert case_progress.get_active_tasks(self.wood_app, False).count() == 0

    def test_bypass_chief_failure(self):
        url = reverse(
            "import:bypass-chief",
            kwargs={"application_pk": self.wood_app.pk, "chief_status": "failure"},
        )
        resp = self.client.post(url)

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.PROCESSING])
        case_progress.check_expected_task(self.wood_app, Task.TaskType.CHIEF_ERROR)

    def test_bypass_chief_variation_request_success(self, test_icms_admin_user):
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        self.wood_app.variation_requests.create(
            status=VariationRequest.OPEN,
            what_varied="Dummy what_varied",
            why_varied="Dummy why_varied",
            when_varied=timezone.now().date(),
            requested_by=test_icms_admin_user,
        )

        self.wood_app.save()

        url = reverse(
            "import:bypass-chief",
            kwargs={"application_pk": self.wood_app.pk, "chief_status": "success"},
        )
        resp = self.client.post(url)

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.COMPLETED])
        assert case_progress.get_active_tasks(self.wood_app, False).count() == 0

        vr = self.wood_app.variation_requests.first()
        assert vr.status == VariationRequest.ACCEPTED
