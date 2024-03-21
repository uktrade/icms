import binascii
import datetime as dt
import os
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings, signals
from django.test.client import Client
from django.urls import reverse
from freezegun import freeze_time
from jinja2 import Template as Jinja2Template
from notifications_python_client import NotificationsAPIClient
from pytest_django.asserts import assertRedirects

from web.auth.fox_hasher import FOXPBKDF2SHA1Hasher
from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import end_process_task
from web.domains.signature import utils as signature_utils
from web.flow.models import ProcessTypes
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    ChecklistFirearmsOILApplication,
    Country,
    DFLApplication,
    DFLChecklist,
    Exporter,
    ExporterAccessRequest,
    File,
    ImportContact,
    Importer,
    ImporterAccessRequest,
    Mailshot,
    Office,
    OpenIndividualLicenceApplication,
    Report,
    SanctionsAndAdhocApplication,
    ScheduleReport,
    Signature,
    SILApplication,
    SILChecklist,
    Task,
    User,
    WoodQuotaApplication,
    WoodQuotaChecklist,
)
from web.models.shared import YesNoNAChoices
from web.reports.constants import DateFilterType, ReportType
from web.sites import SiteName
from web.tests.helpers import CaseURLS, get_test_client
from web.tests.utils.search.conftest import Build, importer_one_fixture_data  # NOQA

from .application_utils import (
    create_in_progress_cfs_app,
    create_in_progress_com_app,
    create_in_progress_fa_dfl_app,
    create_in_progress_fa_oil_app,
    create_in_progress_fa_sil_app,
    create_in_progress_gmp_app,
    create_in_progress_sanctions_app,
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

LOGIN_URL = reverse("accounts:login")


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


#
# Site Fixtures
#
@pytest.fixture()
def caseworker_site(db):
    return Site.objects.get(name=SiteName.CASEWORKER)


@pytest.fixture()
def importer_site(db):
    return Site.objects.get(name=SiteName.IMPORTER)


@pytest.fixture()
def exporter_site(db):
    return Site.objects.get(name=SiteName.EXPORTER)


#
# Client Fixtures
#
@pytest.fixture()
def cw_client(caseworker_site):
    """Client used to access caseworker site.

    No user is logged in with this client.
    """
    return get_test_client(caseworker_site.domain)


@pytest.fixture()
def exp_client(exporter_site):
    """Client used to access exporter site.

    No user is logged in with this client.
    """
    return get_test_client(exporter_site.domain)


@pytest.fixture()
def imp_client(importer_site):
    """Client used to access importer site.

    No user is logged in with this client.
    """
    return get_test_client(importer_site.domain)


@pytest.fixture()
def ilb_admin_client(ilb_admin_user, caseworker_site) -> Client:
    return get_test_client(caseworker_site.domain, ilb_admin_user)


@pytest.fixture()
def ilb_admin_two_client(ilb_admin_two, caseworker_site) -> Client:
    return get_test_client(caseworker_site.domain, ilb_admin_two)


@pytest.fixture()
def nca_admin_client(nca_admin_user, caseworker_site) -> Client:
    return get_test_client(caseworker_site.domain, nca_admin_user)


@pytest.fixture()
def ho_admin_client(ho_admin_user, caseworker_site) -> Client:
    return get_test_client(caseworker_site.domain, ho_admin_user)


@pytest.fixture()
def constabulary_client(constabulary_contact, caseworker_site) -> Client:
    return get_test_client(caseworker_site.domain, constabulary_contact)


@pytest.fixture()
def importer_client(importer_one_contact, importer_site) -> Client:
    return get_test_client(importer_site.domain, importer_one_contact)


@pytest.fixture()
def importer_agent_client(importer_one_agent_one_contact, importer_site) -> Client:
    return get_test_client(importer_site.domain, importer_one_agent_one_contact)


@pytest.fixture()
def exporter_client(exporter_one_contact, exporter_site) -> Client:
    return get_test_client(exporter_site.domain, exporter_one_contact)


@pytest.fixture()
def exporter_two_client(exporter_two_contact, exporter_site) -> Client:
    return get_test_client(exporter_site.domain, exporter_two_contact)


@pytest.fixture()
def exporter_agent_client(exporter_one_agent_one_contact, exporter_site) -> Client:
    return get_test_client(exporter_site.domain, exporter_one_agent_one_contact)


@pytest.fixture()
def report_user_client(report_user, caseworker_site) -> Client:
    return get_test_client(caseworker_site.domain, report_user)


#
# User fixtures
#
@pytest.fixture
def ilb_admin_user(django_user_model):
    """Fixture to get user with admin access (the ilb_admin permission)."""
    return django_user_model.objects.get(username="ilb_admin_user")


@pytest.fixture
def nca_admin_user(django_user_model):
    """Fixture to get an NCA Case Officer user."""
    return django_user_model.objects.get(username="nca_admin_user")


@pytest.fixture
def ho_admin_user(django_user_model):
    """Fixture to get a Home Office Case Officer user."""
    return django_user_model.objects.get(username="ho_admin_user")


@pytest.fixture
def san_admin_user(django_user_model):
    """Fixture to get a Sanctions Case Officer user."""
    return django_user_model.objects.get(username="san_admin_user")


@pytest.fixture
def import_search_user(django_user_model):
    """Fixture to get a Import Search user."""
    return django_user_model.objects.get(username="import_search_user")


@pytest.fixture
def report_user(django_user_model):
    """Fixture to get a Reports user."""
    return django_user_model.objects.get(username="report_user")


@pytest.fixture
def ilb_admin_two(django_user_model):
    return django_user_model.objects.get(username="ilb_admin_two")


@pytest.fixture
def importer_one_contact(django_user_model):
    """Fixture to get user who is a contact of the test importer."""
    return django_user_model.objects.get(username="I1_main_contact")


@pytest.fixture()
def importer_one_agent_one_contact(django_user_model):
    return django_user_model.objects.get(username="I1_A1_main_contact")


@pytest.fixture()
def importer_two_contact(django_user_model):
    return django_user_model.objects.get(username="I2_main_contact")


@pytest.fixture()
def exporter_one_contact(django_user_model):
    return django_user_model.objects.get(username="E1_main_contact")


@pytest.fixture()
def exporter_one_agent_one_contact(django_user_model):
    return django_user_model.objects.get(username="E1_A1_main_contact")


@pytest.fixture()
def exporter_two_contact(django_user_model):
    return django_user_model.objects.get(username="E2_main_contact")


@pytest.fixture
def access_request_user(django_user_model):
    """Fixture to get user to test access request."""
    return django_user_model.objects.get(username="access_request_user")


@pytest.fixture
def constabulary_contact(django_user_model):
    """Fixture to get constabulary contact user.

    This user is linked to the following constabularies:
      - Nottingham
      - Lincolnshire
      - Derbyshire
    """
    return django_user_model.objects.get(username="con_user")


@pytest.fixture()
def legacy_user(db, fox_hasher_enabled):
    user_email = "legacy_user@example.com"  # /PS-IGNORE
    user = User.objects.create(username=user_email, email=user_email, icms_v1_user=True)

    # Create a legacy password
    hex_bytes = binascii.b2a_hex(os.urandom(15))
    user_salt = f"{user.id}:{hex_bytes.decode()}"
    user.password = make_password("TestPassword1!", salt=user_salt, hasher="fox_pbkdf2_sha1")
    user.save()

    # <algorithm>$<iterations>$<salt>$<hash>
    algorithm, *_ = user.password.split("$")
    assert algorithm == FOXPBKDF2SHA1Hasher.algorithm

    return user


@pytest.fixture()
def one_login_user(db):
    return User.objects.create(
        username="one_login_id", email="one_login_user@example.com"  # /PS-IGNORE
    )


#
# All Other Fixtures
#
@pytest.fixture()
def fox_hasher_enabled():
    with override_settings(
        PASSWORD_HASHERS=[
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
            "web.auth.fox_hasher.FOXPBKDF2SHA1Hasher",
        ]
    ):
        yield None


@pytest.fixture
def importer_access_request(db):
    """Fixture to get an in progress importer access request."""
    return ImporterAccessRequest.objects.get(reference="iar/1")


@pytest.fixture
def exporter_access_request(db):
    """Fixture to get an in progress exporter access request."""
    return ExporterAccessRequest.objects.get(reference="ear/1")


@pytest.fixture
def office(db):
    """Fixture to get an office model instance (linked to Test Importer 1)."""

    return Office.objects.get(
        address_1="I1 address line 1",
        address_2="I1 address line 2",
        postcode="BT180LZ",  # /PS-IGNORE
    )


@pytest.fixture
def importer_one_agent_office(db):
    """Fixture to get an office model instance (linked to Test Importer 1 Agent 1)."""

    return Office.objects.get(address_1="I1_A1 address line 1")


@pytest.fixture
def exporter_office(db):
    """Fixture to get an office model instance (linked to exporter)."""
    return Office.objects.get(
        address_1="E1 address line 1",
        address_2="E1 address line 2",
        postcode="HG15DB",  # /PS-IGNORE
    )


@pytest.fixture
def exporter_two_office(db):
    return Office.objects.get(address_1="E2 address line 1")


@pytest.fixture
def exporter_one_agent_one_office(db):
    """Fixture to get an office model instance (linked to Test Exporter 1 Agent 1)."""

    return Office.objects.get(address_1="E1_A1 address line 1")


@pytest.fixture
def importer(db):
    """Fixture to get an importer model instance."""
    return Importer.objects.get(name="Test Importer 1")


@pytest.fixture()
def importer_two(db):
    return Importer.objects.get(name="Test Importer 2")


@pytest.fixture
def agent_importer(db):
    """Fixture to get an Agent Importer model instance."""
    return Importer.objects.get(name="Test Importer 1 Agent 1")


@pytest.fixture
def exporter(db):
    """Fixture to get an Exporter model instance."""
    return Exporter.objects.get(name="Test Exporter 1")


@pytest.fixture
def exporter_two(db):
    """Fixture to get an Exporter model instance."""
    return Exporter.objects.get(name="Test Exporter 2")


@pytest.fixture
def agent_exporter(db):
    """Fixture to get an Agent Exporter model instance."""
    return Exporter.objects.get(name="Test Exporter 1 Agent 1")


@pytest.fixture()
def wood_app_in_progress(
    importer_client, importer, office, importer_one_contact
) -> WoodQuotaApplication:
    """An in progress wood application with a fully valid set of data."""

    app = create_in_progress_wood_app(importer_client, importer, office, importer_one_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def wood_app_submitted(
    importer_client, importer, office, importer_one_contact
) -> WoodQuotaApplication:
    """A valid wood application in the submitted state."""

    app = create_in_progress_wood_app(importer_client, importer, office, importer_one_contact)

    submit_app(client=importer_client, view_name="import:wood:submit-quota", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_dfl_app_in_progress(
    importer_client, importer_one_contact, importer, office
) -> DFLApplication:
    """An in progress FA-DFL application with a fully valid set of data."""

    # Create the FA-DFL app
    app = create_in_progress_fa_dfl_app(importer_client, importer, office, importer_one_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture
def fa_dfl_agent_app_in_progress(
    importer_agent_client,
    importer_one_agent_one_contact,
    importer,
    office,
    agent_importer,
    importer_one_agent_office,
):
    """An in progress FA-DFL agent application with a fully valid set of data."""

    # Create the FA-DFL agent app
    app = create_in_progress_fa_dfl_app(
        importer_agent_client,
        importer,
        office,
        importer_one_agent_one_contact,
        agent_importer,
        importer_one_agent_office,
    )

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def fa_dfl_app_submitted(importer_client, importer, office, importer_one_contact) -> DFLApplication:
    """A valid FA-DFL application in the submitted state."""

    app = create_in_progress_fa_dfl_app(importer_client, importer, office, importer_one_contact)

    submit_app(client=importer_client, view_name="import:fa-dfl:submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_dfl_app_processing(
    importer_client, importer, office, importer_one_contact, ilb_admin_user, ilb_admin_client
) -> DFLApplication:
    app = create_in_progress_fa_dfl_app(importer_client, importer, office, importer_one_contact)
    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    # Taking ownership and begin processing
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    # Set the cover letter, decision, and fill checklist so authorisation can begin
    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()
    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Start authorisation
    ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))

    case_progress.check_expected_status(app, [ImpExpStatus.PROCESSING])
    case_progress.check_expected_task(app, Task.TaskType.AUTHORISE)

    return app


@pytest.fixture()
def fa_dfl_agent_app_submitted(
    importer_agent_client,
    importer_one_agent_one_contact,
    importer,
    office,
    agent_importer,
    importer_one_agent_office,
):
    """A valid FA-DFL agent application in the submitted state."""

    # Create the FA-DFL agent app
    app = create_in_progress_fa_dfl_app(
        importer_agent_client,
        importer,
        office,
        importer_one_agent_one_contact,
        agent_importer,
        importer_one_agent_office,
    )

    submit_app(client=importer_agent_client, view_name="import:fa-dfl:submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_oil_app_submitted(
    importer_client, importer, office, importer_one_contact
) -> OpenIndividualLicenceApplication:
    """A valid FA OIL application in the submitted state."""

    app = create_in_progress_fa_oil_app(importer_client, importer, office, importer_one_contact)

    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def fa_oil_app_in_progress(
    importer_client, importer, office, importer_one_contact
) -> OpenIndividualLicenceApplication:
    """A valid FA OIL application in the in_progress state."""

    app = create_in_progress_fa_oil_app(importer_client, importer, office, importer_one_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def fa_oil_app_processing(
    importer_client, importer, office, importer_one_contact, ilb_admin_user, ilb_admin_client
) -> OpenIndividualLicenceApplication:
    app = create_in_progress_fa_oil_app(importer_client, importer, office, importer_one_contact)
    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    # Taking ownership and begin processing
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    # Set the cover letter, decision, and fill checklist so authorisation can begin
    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()
    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Start authorisation
    ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))

    case_progress.check_expected_status(app, [ImpExpStatus.PROCESSING])
    case_progress.check_expected_task(app, Task.TaskType.AUTHORISE)

    return app


@pytest.fixture()
def fa_sil_app_in_progress(
    importer_client, importer, office, importer_one_contact
) -> SILApplication:
    app = create_in_progress_fa_sil_app(importer_client, importer, office, importer_one_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def fa_sil_app_processing(
    importer_client, importer, office, importer_one_contact, ilb_admin_user, ilb_admin_client
) -> SILApplication:
    app = create_in_progress_fa_sil_app(importer_client, importer, office, importer_one_contact)
    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    # Taking ownership and begin processing
    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    # Set the cover letter, decision, and fill checklist so authorisation can begin
    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()
    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Start authorisation
    ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))

    case_progress.check_expected_status(app, [ImpExpStatus.PROCESSING])
    case_progress.check_expected_task(app, Task.TaskType.AUTHORISE)

    return app


@pytest.fixture()
def fa_sil_app_submitted(importer_client, importer, office, importer_one_contact) -> SILApplication:
    """A valid FA SIL application in the submitted state."""
    app = create_in_progress_fa_sil_app(importer_client, importer, office, importer_one_contact)

    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def sanctions_app_in_progress(
    importer_client, importer, office, importer_one_contact
) -> SanctionsAndAdhocApplication:
    app = create_in_progress_sanctions_app(importer_client, importer, office, importer_one_contact)

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def sanctions_app_submitted(
    importer_client, importer, office, importer_one_contact
) -> SanctionsAndAdhocApplication:
    app = create_in_progress_sanctions_app(importer_client, importer, office, importer_one_contact)

    submit_app(client=importer_client, view_name=app.get_submit_view_name(), app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def com_app_in_progress(
    exporter_client, exporter, exporter_office, exporter_one_contact
) -> "CertificateOfManufactureApplication":
    # Create the COM app
    app = create_in_progress_com_app(
        exporter_client, exporter, exporter_office, exporter_one_contact
    )

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def com_agent_app_in_progress(
    exporter_agent_client,
    exporter_one_agent_one_contact,
    exporter,
    exporter_office,
    agent_exporter,
    exporter_one_agent_one_office,
) -> "CertificateOfManufactureApplication":
    # Create the COM app
    app = create_in_progress_com_app(
        exporter_agent_client,
        exporter,
        exporter_office,
        exporter_one_agent_one_contact,
        agent_exporter,
        exporter_one_agent_one_office,
    )

    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture()
def com_app_submitted(
    exporter_client, exporter, exporter_office, exporter_one_contact
) -> "CertificateOfManufactureApplication":
    # Create the COM app
    app = create_in_progress_com_app(
        exporter_client, exporter, exporter_office, exporter_one_contact
    )

    submit_app(client=exporter_client, view_name="export:com-submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def com_agent_app_submitted(
    exporter_agent_client,
    exporter_one_agent_one_contact,
    exporter,
    exporter_office,
    agent_exporter,
    exporter_one_agent_one_office,
) -> "CertificateOfManufactureApplication":
    # Create the COM app
    app = create_in_progress_com_app(
        exporter_agent_client,
        exporter,
        exporter_office,
        exporter_one_agent_one_contact,
        agent_exporter,
        exporter_one_agent_one_office,
    )

    submit_app(client=exporter_agent_client, view_name="export:com-submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def gmp_app_submitted(
    exporter_client, exporter, exporter_office, exporter_one_contact
) -> CertificateOfGoodManufacturingPracticeApplication:
    app = create_in_progress_gmp_app(
        exporter_client, exporter, exporter_office, exporter_one_contact
    )
    submit_app(client=exporter_client, view_name="export:gmp-submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def cfs_app_submitted(
    exporter_client, exporter, exporter_office, exporter_one_contact
) -> CertificateOfFreeSaleApplication:
    app = create_in_progress_cfs_app(
        exporter_client, exporter, exporter_office, exporter_one_contact
    )
    submit_app(client=exporter_client, view_name="export:cfs-submit", app_pk=app.pk)

    app.refresh_from_db()

    case_progress.check_expected_status(app, [ImpExpStatus.SUBMITTED])
    case_progress.check_expected_task(app, Task.TaskType.PROCESS)

    return app


@pytest.fixture()
def cfs_app_in_progress(
    exporter_client, exporter, exporter_office, exporter_one_contact
) -> CertificateOfFreeSaleApplication:
    app = create_in_progress_cfs_app(
        exporter_client, exporter, exporter_office, exporter_one_contact
    )
    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)

    return app


@pytest.fixture
def completed_sil_app(fa_sil_app_submitted, ilb_admin_client, ilb_admin_user):
    """A completed firearms sil application."""
    app = fa_sil_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


@pytest.fixture
def completed_sil_app_with_supplementary_report(completed_sil_app, importer_client):
    app = completed_sil_app
    report = _add_supplementary_report_to_app(app, importer_client)
    add_section_1_firearm_url = CaseURLS.fa_sil_report_manual_add(
        app.pk, report.pk, app.goods_section1.first().pk, "section1"
    )
    importer_client.post(
        add_section_1_firearm_url,
        data={
            "calibre": "1mm",
            "model": "Test-Section1",
            "proofing": "yes",
            "serial_number": "11111111111",
        },
    )

    add_section_5_firearm_url = CaseURLS.fa_sil_report_manual_add(
        app.pk, report.pk, app.goods_section5.first().pk, "section5"
    )
    importer_client.post(
        add_section_5_firearm_url,
        data={
            "calibre": "5mm",
            "model": "Test-Section5",
            "proofing": "no",
            "serial_number": "555555555555",
        },
    )
    add_section_2_firearm_url = CaseURLS.fa_sil_report_manual_add(
        app.pk, report.pk, app.goods_section2.first().pk, "section2"
    )
    importer_client.post(
        add_section_2_firearm_url,
        data={
            "calibre": "2mm",
            "model": "Test-Section2",
            "proofing": "no",
            "serial_number": "22222222222",
        },
    )
    add_section_5_ob_firearm_url = CaseURLS.fa_sil_report_manual_add(
        app.pk, report.pk, app.goods_section582_obsoletes.first().pk, "section582-obsolete"
    )
    importer_client.post(
        add_section_5_ob_firearm_url,
        data={
            "calibre": "5.1mm",
            "model": "Test-Section5-Obsolete",
            "proofing": "no",
            "serial_number": "5555555555551",
        },
    )
    add_section_5_other_firearm_url = CaseURLS.fa_sil_report_manual_add(
        app.pk, report.pk, app.goods_section582_others.first().pk, "section582-other"
    )
    importer_client.post(
        add_section_5_other_firearm_url,
        data={
            "calibre": "5.2mm",
            "model": "Test-Section5Others",
            "proofing": "no",
            "serial_number": "5555555555552",
        },
    )
    app.refresh_from_db()
    return app


@pytest.fixture
def completed_oil_app_with_supplementary_report(completed_oil_app, importer_client):
    app = completed_oil_app
    report = _add_supplementary_report_to_app(app, importer_client)
    add_report_url = CaseURLS.fa_oil_report_upload_add(app.pk, report.pk)
    importer_client.post(
        add_report_url,
        data={"file": SimpleUploadedFile("myimage.png", b"file_content")},
    )
    app.refresh_from_db()
    return app


@pytest.fixture
def completed_dfl_app_with_supplementary_report(completed_dfl_app, importer_client):
    app = completed_dfl_app
    report = _add_supplementary_report_to_app(app, importer_client)
    add_report_url = CaseURLS.fa_dfl_report_manual_add(
        app.pk, report.pk, app.goods_certificates.first().pk
    )
    importer_client.post(
        add_report_url,
        data={
            "calibre": "4.1mm",
            "model": "DFL Firearm",
            "proofing": "yes",
            "serial_number": "5555555555552",
        },
    )
    app.refresh_from_db()
    return app


def _add_supplementary_report_to_app(app, client):
    # Add import contact
    create_import_contact_url = CaseURLS.fa_create_import_contact(app.pk, ImportContact.LEGAL)
    add_contact_data = {
        "first_name": "first_name value",
        "registration_number": "registration_number value",
        "street": "street value",
        "city": "city value",
        "postcode": "postcode value",
        "region": "region value",
        "country": Country.objects.first().pk,
        "dealer": "yes",
    }

    client.post(create_import_contact_url, data=add_contact_data)
    create_report_url = CaseURLS.fa_create_report(app.pk)
    response = client.get(create_report_url)
    contact_pk = response.context["form"].fields["bought_from"].queryset.first().pk

    # Add Report
    client.post(
        create_report_url,
        data={
            "bought_from": contact_pk,
            "date_received": "13-Feb-2024",
            "transport": "air",
        },
    )
    return app.supplementary_info.reports.first()


@pytest.fixture
def completed_oil_app(fa_oil_app_submitted, ilb_admin_client, ilb_admin_user):
    """A completed firearms oil application."""
    app = fa_oil_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


@pytest.fixture
def completed_sps_app(importer_one_fixture_data, ilb_admin_client, ilb_admin_user):  # NOQA
    with freeze_time("2024-01-01 12:00:00"):
        app = Build.sps_application(
            "sps app 1",
            importer_one_fixture_data,
            origin_country="Afghanistan",
            consignment_country="Armenia",
            commodity_code="111111",
        )
        ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


def _set_document_pack_active(app):
    with freeze_time(app.submit_datetime) as frozen_datetime:
        frozen_datetime.tick(delta=dt.timedelta(days=1, hours=5, minutes=2))
        document_pack.pack_draft_set_active(app)


@pytest.fixture
def completed_wood_app(wood_app_submitted, ilb_admin_client, ilb_admin_user):
    """A completed wood application."""
    app = wood_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    licence = _set_valid_licence(app)
    licence.issue_paper_licence_only = True
    licence.save()

    _add_valid_checklist(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


@pytest.fixture
def completed_dfl_app(fa_dfl_app_submitted, ilb_admin_client, ilb_admin_user):
    """A completed firearms dfl application."""
    app = fa_dfl_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)
    _add_valid_checklist(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


@pytest.fixture
def completed_sanctions_app(sanctions_app_submitted, ilb_admin_client, ilb_admin_user):
    app = sanctions_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    app.refresh_from_db()
    app.cover_letter_text = "Example Cover letter"
    app.decision = app.APPROVE
    app.save()

    _set_valid_licence(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    # Now fake complete the app
    app.status = ImpExpStatus.COMPLETED
    app.save()

    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)
    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


@pytest.fixture
def completed_cfs_app(cfs_app_submitted, ilb_admin_client, ilb_admin_user):
    """A Certificate of Free Sale (export) application that has been approved."""
    app = cfs_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))

    app.refresh_from_db()
    app.decision = app.APPROVE
    app.save()

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk, "export"))
    assertRedirects(response, reverse("workbasket"), 302)

    app.refresh_from_db()
    app.status = ImpExpStatus.COMPLETED
    app.save()
    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)

    _set_document_pack_active(app)
    _add_files_to_active_document_pack(app, ilb_admin_user)
    return app


@pytest.fixture
def completed_com_app(com_app_submitted, ilb_admin_client):
    """A Certificate of Free Sale (export) application that has been approved."""
    app = com_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))

    app.refresh_from_db()
    app.decision = app.APPROVE
    app.save()

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk, "export"))
    assertRedirects(response, reverse("workbasket"), 302)

    app.refresh_from_db()
    app.status = ImpExpStatus.COMPLETED
    app.save()
    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)

    document_pack.pack_draft_set_active(app)

    return app


@pytest.fixture
def completed_gmp_app(gmp_app_submitted, ilb_admin_client):
    """A Certificate of Free Sale (export) application that has been approved."""
    app = gmp_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))

    app.refresh_from_db()
    app.decision = app.APPROVE
    app.save()

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk, "export"))
    assertRedirects(response, reverse("workbasket"), 302)

    app.refresh_from_db()
    app.status = ImpExpStatus.COMPLETED
    app.save()
    task = case_progress.get_expected_task(app, Task.TaskType.AUTHORISE)
    end_process_task(task)

    document_pack.pack_draft_set_active(app)

    return app


@pytest.fixture
def complete_rejected_export_app(cfs_app_submitted, ilb_admin_client):
    """A Certificate of Free Sale (export) application that has been rejected."""
    app = cfs_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))

    app.refresh_from_db()
    app.decision = app.REFUSE
    app.refuse_reason = "Application Incomplete"
    app.save()

    _set_valid_licence(app)

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk, "export"))
    assertRedirects(response, reverse("workbasket"), 302)

    app.refresh_from_db()
    case_progress.check_expected_status(app, [ImpExpStatus.COMPLETED])
    case_progress.check_expected_task(app, Task.TaskType.REJECTED)
    return app


@pytest.fixture
def complete_rejected_app(fa_sil_app_submitted, ilb_admin_client):
    """A Firearms Specific Import application that has been rejected."""
    app = fa_sil_app_submitted

    ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

    _set_valid_licence(app)
    _add_valid_checklist(app)

    app.decision = app.REFUSE
    app.refuse_reason = "Application Incomplete"
    app.save()

    # Now start authorisation
    response = ilb_admin_client.post(CaseURLS.start_authorisation(app.pk))
    assertRedirects(response, reverse("workbasket"), 302)

    app.refresh_from_db()
    case_progress.check_expected_status(app, [ImpExpStatus.COMPLETED])
    case_progress.check_expected_task(app, Task.TaskType.REJECTED)
    return app


@pytest.fixture
def document_form_data():
    """Used in tests requiring a document to be uploaded in a form."""

    return {"document": SimpleUploadedFile("myimage.png", b"file_content")}


@pytest.fixture
def strict_templates():
    """Ensure strict templates."""
    with override_settings(TEMPLATES=settings.STRICT_TEMPLATES):
        yield None


@pytest.fixture
def enable_gov_notify_backend():
    with override_settings(EMAIL_BACKEND="web.mail.backends.GovNotifyEmailBackend"):
        yield None


@pytest.fixture
def mock_gov_notify_client(enable_gov_notify_backend):
    with mock.patch("web.mail.api.get_gov_notify_client") as client:
        mock_gov_notify_client = mock.create_autospec(
            spec=NotificationsAPIClient(settings.GOV_NOTIFY_API_KEY), instance=True
        )
        client.return_value = mock_gov_notify_client
        yield mock_gov_notify_client


def _set_valid_licence(app):
    licence = document_pack.pack_draft_get(app)
    licence.case_completion_datetime = dt.datetime(2020, 1, 1, tzinfo=dt.UTC)
    licence.licence_start_date = dt.date(2020, 6, 1)
    licence.licence_end_date = dt.date(2024, 12, 31)
    licence.issue_paper_licence_only = False
    licence.save()
    return licence


def _add_valid_checklist(app):
    checklist = {
        "import_application": app,
        "case_update": YesNoNAChoices.yes,
        "fir_required": YesNoNAChoices.yes,
        "response_preparation": True,
        "validity_period_correct": YesNoNAChoices.yes,
        "endorsements_listed": YesNoNAChoices.yes,
        "authorisation": True,
    }
    match app.process_type:
        case ProcessTypes.FA_SIL:
            app.checklist = SILChecklist.objects.create(
                **checklist
                | {
                    "authority_required": YesNoNAChoices.yes,
                    "authority_received": YesNoNAChoices.yes,
                    "authority_cover_items_listed": YesNoNAChoices.yes,
                    "quantities_within_authority_restrictions": YesNoNAChoices.yes,
                    "authority_police": YesNoNAChoices.yes,
                }
            )
        case ProcessTypes.FA_DFL:
            app.checklist = DFLChecklist.objects.create(
                **checklist
                | {
                    "deactivation_certificate_attached": YesNoNAChoices.yes,
                    "deactivation_certificate_issued": YesNoNAChoices.yes,
                }
            )
        case ProcessTypes.FA_OIL:
            app.checklist = ChecklistFirearmsOILApplication.objects.create(
                **checklist
                | {
                    "authority_required": YesNoNAChoices.yes,
                    "authority_received": YesNoNAChoices.yes,
                    "authority_police": YesNoNAChoices.yes,
                }
            )
        case ProcessTypes.WOOD:
            app.checklist = WoodQuotaChecklist.objects.create(
                **checklist
                | {
                    "sigl_wood_application_logged": True,
                }
            )
        case _:
            raise ValueError(f"Invalid process_type: {app.process_type}")


def _add_files_to_active_document_pack(app, ilb_admin_user) -> None:
    """Simulates what happens when upload_case_document_file is called without uploading a file to s3"""
    active_pack = document_pack.pack_active_get(app)

    for cdr in active_pack.document_references.all():
        cdr.document = File.objects.create(
            is_active=True,
            filename=f"{cdr.document_type}.pdf",
            content_type="application/pdf",
            file_size=10,
            path=f"{cdr.document_type}.pdf",
            created_by=ilb_admin_user,
        )
        cdr.save()


@pytest.fixture
def draft_mailshot(ilb_admin_user):
    return Mailshot.objects.create(
        email_body="original message",
        email_subject="original subject",
        retract_email_body="retract message",
        retract_email_subject="retract subject",
        created_by=ilb_admin_user,
        is_email=True,
        title="Test Mailshot",
        description="A mailshot to use for testing",
        status=Mailshot.Statuses.DRAFT,
    )


@pytest.fixture()
def active_signature():
    return Signature.objects.get(name="Test Active Signature", is_active=True)


@pytest.fixture(autouse=True)
def mock_signature_file(monkeypatch):
    mock_file = mock.create_autospec(signature_utils.get_signature_file_base64)
    mock_file.return_value = ""
    monkeypatch.setattr(signature_utils, "get_signature_file_base64", mock_file)


@pytest.fixture
def report_schedule(report_user):
    issued_cert_report = Report.objects.get(report_type=ReportType.ISSUED_CERTIFICATES)
    return ScheduleReport.objects.create(
        report=issued_cert_report,
        title="test report",
        scheduled_by=report_user,
        notes="",
        parameters={
            "date_from": "2010-02-01",
            "date_to": "2024-01-12",
            "date_filter_type": DateFilterType.SUBMITTED,
            "application_type": "",
            "legislation": [],
        },
    )
