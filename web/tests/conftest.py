import pytest
from django.core.management import call_command
from django.test import signals
from jinja2 import Template as Jinja2Template

from web.domains.case.access.models import ExporterAccessRequest, ImporterAccessRequest
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.office.models import Office

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
        call_command("add_test_data")


@pytest.fixture
def test_icms_admin_user(django_user_model):
    """Fixture to get user with admin access (the reference_data_access permission)."""
    return django_user_model.objects.get(username="test_icms_admin_user")


@pytest.fixture
def test_import_user(django_user_model):
    """Fixture to get user with access to the test importer."""
    return django_user_model.objects.get(username="test_import_user")


@pytest.fixture
def test_agent_import_user(django_user_model):
    """Fixture to get agent user with access to the test importer."""
    return django_user_model.objects.get(username="test_agent_import_user")


@pytest.fixture
def test_export_user(django_user_model):
    """Fixture to get user with access to the test exporter."""
    return django_user_model.objects.get(username="test_export_user")


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
def importer_contact(django_user_model):
    """Fixture to get user who is a contact of the test importer."""
    return django_user_model.objects.get(username="importer_contact")


@pytest.fixture
def office():
    """Fixture to get an office model instance."""
    return Office.objects.get(is_active=True, address="47 some way, someplace", postcode="S410SG")


@pytest.fixture
def importer():
    """Fixture to get an importer model instance."""
    return Importer.objects.get(
        is_active=True,
        type=Importer.INDIVIDUAL,
        region_origin=Importer.UK,
        name="UK based importer",
        main_importer=None,
    )


@pytest.fixture
def agent_importer(importer):
    """Fixture to get an Agent Importer model instance."""
    return Importer.objects.get(
        is_active=True,
        type=Importer.INDIVIDUAL,
        region_origin=Importer.UK,
        name="UK based importer",
        main_importer=importer,
    )


@pytest.fixture
def exporter():
    """Fixture to get an Exporter model instance."""
    return Exporter.objects.get(
        is_active=True, name="UK based exporter", registered_number="422", main_exporter=None
    )


@pytest.fixture
def agent_exporter(exporter):
    """Fixture to get an Agent Exporter model instance."""
    return Exporter.objects.get(
        is_active=True, name="UK based exporter", registered_number="422", main_exporter=exporter
    )
