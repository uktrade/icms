import pytest
from django.core.exceptions import PermissionDenied
from guardian.shortcuts import assign_perm, remove_perm

from web.domains.case.views import check_application_permission
from web.tests.domains.case._import.factory import OILApplicationFactory
from web.tests.domains.case.access.factories import (
    ExporterAccessRequestFactory,
    ImporterAccessRequestFactory,
)
from web.tests.domains.case.export.factories import (
    CertificateOfManufactureApplicationFactory,
)
from web.tests.domains.exporter.factory import ExporterFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import ActiveUserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def ilb_admin_user():
    return ActiveUserFactory.create(permission_codenames=["reference_data_access"])


@pytest.fixture
def imp_application_user():
    return ActiveUserFactory.create(permission_codenames=["importer_access"])


@pytest.fixture
def exp_application_user():
    return ActiveUserFactory.create(permission_codenames=["exporter_access"])


@pytest.fixture
def access_application_user():
    return ActiveUserFactory.create()


@pytest.fixture
def import_application(imp_application_user):
    user = imp_application_user

    importer = ImporterFactory.create(user=user)

    assign_perm("web.is_contact_of_importer", user, importer)

    return OILApplicationFactory.create(
        status="SUBMITTED", importer=importer, created_by=user, last_updated_by=user
    )


@pytest.fixture
def export_application(exp_application_user):
    user = exp_application_user
    exporter = ExporterFactory.create()

    assign_perm("web.is_contact_of_exporter", user, exporter)

    return CertificateOfManufactureApplicationFactory.create(
        status="SUBMITTED", exporter=exporter, created_by=user, last_updated_by=user
    )


@pytest.fixture
def import_access_request_application(access_application_user):
    user = access_application_user

    return ImporterAccessRequestFactory.create(
        status="SUBMITTED",
        submitted_by=user,
        last_updated_by=user,
        reference="iar/1",
    )


@pytest.fixture
def export_access_request_application(access_application_user):
    user = access_application_user

    return ExporterAccessRequestFactory.create(
        status="SUBMITTED",
        submitted_by=user,
        last_updated_by=user,
        reference="ear/1",
    )


# ILB admin tests
def test_admin_valid_all_types(
    import_application,
    export_application,
    import_access_request_application,
    export_access_request_application,
    ilb_admin_user,
):
    check_application_permission(import_application, ilb_admin_user, "import")
    check_application_permission(export_application, ilb_admin_user, "export")
    check_application_permission(import_access_request_application, ilb_admin_user, "access")
    check_application_permission(export_access_request_application, ilb_admin_user, "access")


# Import tests
def test_import_application_valid(import_application, imp_application_user):
    check_application_permission(import_application, imp_application_user, "import")


def test_import_application_missing_importer_access_permission(
    import_application, imp_application_user
):
    with pytest.raises(PermissionDenied):
        remove_perm("web.importer_access", imp_application_user)
        check_application_permission(import_application, imp_application_user, "import")


def test_import_application_missing_is_contact_of_importer_permission(
    import_application, imp_application_user
):
    with pytest.raises(PermissionDenied):
        remove_perm("web.is_contact_of_importer", imp_application_user, import_application.importer)
        check_application_permission(import_application, imp_application_user, "import")


# Export Tests
def test_export_application_valid(export_application, exp_application_user):
    check_application_permission(export_application, exp_application_user, "export")


def test_application_missing_exporter_access_permission(export_application, exp_application_user):
    with pytest.raises(PermissionDenied):
        remove_perm("web.exporter_access", exp_application_user)
        check_application_permission(export_application, exp_application_user, "export")


def test_export_application_missing_is_contact_of_exporter_permission(
    export_application, exp_application_user
):
    with pytest.raises(PermissionDenied):
        remove_perm("web.is_contact_of_exporter", exp_application_user, export_application.exporter)
        check_application_permission(export_application, exp_application_user, "export")


# Access Tests
def test_access_application_valid(
    import_access_request_application, export_access_request_application, access_application_user
):
    check_application_permission(
        import_access_request_application, access_application_user, "access"
    )
    check_application_permission(
        export_access_request_application, access_application_user, "access"
    )


def test_access_application_denied_for_different_user(
    import_access_request_application, export_access_request_application
):
    another_user = ActiveUserFactory.create()

    with pytest.raises(PermissionDenied):
        check_application_permission(import_access_request_application, another_user, "access")

    with pytest.raises(PermissionDenied):
        check_application_permission(import_access_request_application, another_user, "access")


# Invalid case_type test
def test_invalid_case_type(import_application, imp_application_user):
    with pytest.raises(PermissionDenied):
        check_application_permission(import_application, imp_application_user, "something-invalid")
