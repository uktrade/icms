import datetime

import pytest
from django.core.management import call_command
from django.test import signals
from django.test.client import Client
from django.urls import reverse
from jinja2 import Template as Jinja2Template
from pytest_django.asserts import assertRedirects

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import end_process_task
from web.models import (
    CertificateOfManufactureApplication,
    DFLApplication,
    Exporter,
    ExporterAccessRequest,
    Importer,
    ImporterAccessRequest,
    Office,
    OpenIndividualLicenceApplication,
    SILApplication,
    SILChecklist,
    Task,
    WoodQuotaApplication,
)
from web.models.shared import YesNoNAChoices
from web.tests.helpers import CaseURLS, get_test_client

from .application_utils import (
    create_in_progress_com_app,
    create_in_progress_fa_dfl_app,
    create_in_progress_fa_oil_app,
    create_in_progress_fa_sil_app,
    create_in_progress_wood_app,
    submit_app,
)

ORIGINAL_JINJA2_RENDERER = Jinja2Template.render


# this is needed to make response.context show up since we are using jinja2
# https://stackoverflow.com/questions/1941980/how-can-i-access-response-context-when-testing-a-jinja2-powered-django-view
def instrumented_render(template_object, *args, **kwargs):
    context = dict(*args, **kwargs)

    signals.template_rendered.send(
        sender=template_object, template=template_object, context=context
    )

    return ORIGINAL_JINJA2_RENDERER(template_object, *args, **kwargs)


Jinja2Template.render = instrumented_render


# https://pytest-django.readthedocs.io/en/latest/database.html#populate-the-test-database-if-you-don-t-use-transactional-or-live-server
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create data when setting up the database.

    This data is not lost between test runs if the db is reused
    See the following file for what data gets added:
        web/management/commands/add_test_data.py
    """

    with django_db_blocker.unblock():
        call_command("create_icms_groups")
        call_command("add_test_data")


@pytest.fixture
def test_icms_admin_user(django_user_model):
    """Fixture to get user with admin access (the ilb_admin permission)."""
    return django_user_model.objects.get(username="test_icms_admin_user")


@pytest.fixture
def test_import_user(django_user_model):
    """Fixture to get user with access to the test importer."""
    return django_user_model.objects.get(username="test_import_user")


@pytest.fixture
def importer_contact(django_user_model):
    """Fixture to get user who is a contact of the test importer."""
    return django_user_model.objects.get(username="importer_contact")


@pytest.fixture()
def importer_one_main_contact(django_user_model):
    return django_user_model.objects.get(username="I1_main_contact")


@pytest.fixture()
def importer_one_agent_one_contact(django_user_model):
    return django_user_model.objects.get(username="I1_A1_main_contact")


@pytest.fixture()
def importer_two_main_contact(django_user_model):
    return django_user_model.objects.get(username="I2_main_contact")


@pytest.fixture
def test_agent_import_user(django_user_model):
    """Fixture to get agent user with access to the test importer."""
    return django_user_model.objects.get(username="test_agent_import_user")


@pytest.fixture
def test_export_user(django_user_model):
    """Fixture to get user with access to the test exporter."""
    return django_user_model.objects.get(username="test_export_user")


@pytest.fixture
def exporter_contact(django_user_model):
    """Fixture to get the user who is a contact of the test exporter."""
    return django_user_model.objects.get(username="exporter_contact")


@pytest.fixture()
def exporter_one_main_contact(django_user_model):
    return django_user_model.objects.get(username="E1_main_contact")


@pytest.fixture()
def exporter_two_main_contact(django_user_model):
    return django_user_model.objects.get(username="E2_main_contact")


@pytest.fixture
def test_agent_export_user(django_user_model):
    """Fixture to get agent user with access to the test exporter."""
    return django_user_model.objects.get(username="test_agent_export_user")


@pytest.fixture
def test_access_user(django_user_model):
    """Fixture to get user to test access request."""
    return django_user_model.objects.get(username="test_access_user")


@pytest.fixture
def import_access_request_application(test_access_user):
    return ImporterAccessRequest.objects.get(
        request_type="MAIN_IMPORTER_ACCESS",
        status="SUBMITTED",
        submitted_by=test_access_user,
        last_updated_by=test_access_user,
        reference="iar/1",
    )


@pytest.fixture
def export_access_request_application(test_access_user):
    return ExporterAccessRequest.objects.get(
        request_type="MAIN_EXPORTER_ACCESS",
        status="SUBMITTED",
        submitted_by=test_access_user,
        last_updated_by=test_access_user,
        reference="ear/1",
    )


@pytest.fixture
def office():
    """Fixture to get an office model instance (linked to Test Importer 1)."""

    return Office.objects.get(
        address_1="I1 address line 1",
        address_2="I1 address line 2",
        postcode="BT180LZ",  # /PS-IGNORE
    )


@pytest.fixture
def importer_one_agent_office():
    """Fixture to get an office model instance (linked to Test Importer 1 Agent 1)."""

    return Office.objects.get(address_1="I1_A1 address line 1")


@pytest.fixture
def exporter_office():
    """Fixture to get an office model instance (linked to exporter)."""
    return Office.objects.get(
        address_1="E1 address line 1",
        address_2="E1 address line 2",
        postcode="HG15DB",  # /PS-IGNORE
    )


@pytest.fixture
def importer():
    """Fixture to get an importer model instance."""
    return Importer.objects.get(name="Test Importer 1")


@pytest.fixture()
def importer_two():
    return Importer.objects.get(name="Test Importer 2")


@pytest.fixture
def agent_importer():
    """Fixture to get an Agent Importer model instance."""
    return Importer.objects.get(name="Test Importer 1 Agent 1")


@pytest.fixture
def exporter():
    """Fixture to get an Exporter model instance."""
    return Exporter.objects.get(name="Test Exporter 1")


@pytest.fixture
def exporter_two():
    """Fixture to get an Exporter model instance."""
    return Exporter.objects.get(name="Test Exporter 2")


@pytest.fixture
def agent_exporter():
    """Fixture to get an Agent Exporter model instance."""
    return Exporter.objects.get(name="Test Exporter 1 Agent 1")


@pytest.fixture()
def icms_admin_client(test_icms_admin_user) -> Client:
    return get_test_client(test_icms_admin_user)


@pytest.fixture()
def importer_client(importer_one_main_contact) -> Client:
    # TODO: Make fixtures more consistent:
    #       rename all test_ fixtures
    #       change all occurrences of test_import_user to use importer_one_main_contact user.
    return get_test_client(importer_one_main_contact)


@pytest.fixture()
def wood_app_in_progress(
    importer_client, importer, office, test_import_user
) -> WoodQuotaApplication:
    """An in progress wood application with a fully valid set of data."""

    app = create_in_progress_wood_app(importer_client, importer, office, test_import_user)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def wood_app_submitted(importer_client, importer, office, test_import_user) -> WoodQuotaApplication:
    """A valid wood application in the submitted state."""

    app = create_in_progress_wood_app(importer_client, importer, office, test_import_user)

    submit_app(client=importer_client, view_name="import:wood:submit-quota", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_dfl_app_in_progress(
    importer_client, test_import_user, importer, office, importer_contact
) -> DFLApplication:
    """An in progress wood application with a fully valid set of data."""

    # Create the FA-DFL app
    app = create_in_progress_fa_dfl_app(importer_client, importer, office, importer_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def fa_dfl_app_submitted(importer_client, importer, office, importer_contact) -> DFLApplication:
    """A valid FA DFL application in the submitted state."""

    app = create_in_progress_fa_dfl_app(importer_client, importer, office, importer_contact)

    submit_app(client=importer_client, view_name="import:fa-dfl:submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_oil_app_submitted(
    importer_client, importer, office, importer_contact
) -> OpenIndividualLicenceApplication:
    """A valid FA OIL application in the submitted state."""

    app = create_in_progress_fa_oil_app(importer_client, importer, office, importer_contact)

    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_sil_app_submitted(importer_client, importer, office, importer_contact) -> SILApplication:
    """A valid FA SIL application in the submitted state."""
    app = create_in_progress_fa_sil_app(importer_client, importer, office, importer_contact)

    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def exporter_client(test_export_user) -> Client:
    return get_test_client(test_export_user)


@pytest.fixture()
def com_app_in_progress(
    exporter_client, exporter, exporter_office, exporter_contact
) -> "CertificateOfManufactureApplication":
    # Create the COM app
    app = create_in_progress_com_app(exporter_client, exporter, exporter_office, exporter_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def com_app_submitted(
    exporter_client, exporter, exporter_office, exporter_contact
) -> "CertificateOfManufactureApplication":
    # Create the COM app
    app = create_in_progress_com_app(exporter_client, exporter, exporter_office, exporter_contact)

    submit_app(client=exporter_client, view_name="export:com-submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture
def completed_app(fa_sil_app_submitted, icms_admin_client):
    """A completed firearms sil application."""
    app = fa_sil_app_submitted

    icms_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Now start authorisation
    response = icms_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    document_pack.pack_draft_set_active(app)

    return app


def _set_valid_licence(app):
    licence = document_pack.pack_draft_get(app)
    licence.case_completion_datetime = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
    licence.licence_start_date = datetime.date(2020, 6, 1)
    licence.licence_end_date = datetime.date(2024, 12, 31)
    licence.issue_paper_licence_only = False
    licence.save()


def _add_valid_checklist(app):
    app.checklist = SILChecklist.objects.create(
        import_application=app,
        case_update=YesNoNAChoices.yes,
        fir_required=YesNoNAChoices.yes,
        response_preparation=True,
        validity_period_correct=YesNoNAChoices.yes,
        endorsements_listed=YesNoNAChoices.yes,
        authorisation=True,
        authority_required=YesNoNAChoices.yes,
        authority_received=YesNoNAChoices.yes,
        authority_cover_items_listed=YesNoNAChoices.yes,
        quantities_within_authority_restrictions=YesNoNAChoices.yes,
        authority_police=YesNoNAChoices.yes,
    )
