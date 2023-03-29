import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from guardian.shortcuts import remove_perm

from web.domains.case.utils import check_application_permission
from web.models import (
    CertificateOfManufactureApplication,
    ExportApplicationType,
    ImportApplicationType,
    OpenIndividualLicenceApplication,
)
from web.permissions import Perms
from web.tests.domains.user.factory import ActiveUserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def import_application(importer, test_import_user):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status="SUBMITTED",
        importer=importer,
        created_by=test_import_user,
        last_updated_by=test_import_user,
    )


@pytest.fixture
def agent_import_application(importer, agent_importer, test_agent_import_user):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status="SUBMITTED",
        importer=importer,
        created_by=test_agent_import_user,
        last_updated_by=test_agent_import_user,
        agent=agent_importer,
    )


@pytest.fixture
def export_application(exporter, test_export_user):
    return CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ),
        status="SUBMITTED",
        exporter=exporter,
        created_by=test_export_user,
        last_updated_by=test_export_user,
    )


@pytest.fixture
def agent_export_application(exporter, agent_exporter, test_agent_export_user):
    return CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ),
        status="SUBMITTED",
        exporter=exporter,
        created_by=test_agent_export_user,
        last_updated_by=test_agent_export_user,
        agent=agent_exporter,
    )


# ILB admin tests
def test_admin_valid_all_types(
    import_application,
    export_application,
    import_access_request_application,
    export_access_request_application,
    test_icms_admin_user,
):
    check_application_permission(import_application, test_icms_admin_user, "import")
    check_application_permission(export_application, test_icms_admin_user, "export")
    check_application_permission(import_access_request_application, test_icms_admin_user, "access")
    check_application_permission(export_access_request_application, test_icms_admin_user, "access")


# Import tests
def test_import_application_valid(import_application, test_import_user):
    check_application_permission(import_application, test_import_user, "import")


def test_import_application_missing_importer_access_permission(
    import_application, test_import_user
):
    with pytest.raises(PermissionDenied):
        group = Group.objects.get(name=Perms.obj.importer.get_group_name())
        test_import_user.groups.remove(group)
        check_application_permission(import_application, test_import_user, "import")


def test_import_application_missing_is_contact_of_importer_permission(
    import_application, test_import_user
):
    with pytest.raises(PermissionDenied):
        remove_perm("web.is_contact_of_importer", test_import_user, import_application.importer)
        check_application_permission(import_application, test_import_user, "import")


# Agent for importer tests
def test_import_agent_application_valid(agent_import_application, test_agent_import_user):
    check_application_permission(agent_import_application, test_agent_import_user, "import")


def test_import_agent_application_missing_importer_access_permission(
    agent_import_application, test_agent_import_user
):
    with pytest.raises(PermissionDenied):
        group = Group.objects.get(name=Perms.obj.importer.get_group_name())
        test_agent_import_user.groups.remove(group)
        check_application_permission(agent_import_application, test_agent_import_user, "import")


def test_import_agent_application_missing_is_contact_of_importer_permission(
    agent_import_application, test_agent_import_user
):
    with pytest.raises(PermissionDenied):
        remove_perm(
            "web.is_agent_of_importer",
            test_agent_import_user,
            agent_import_application.importer,
        )
        check_application_permission(agent_import_application, test_agent_import_user, "import")


# Export Tests
def test_export_application_valid(export_application, test_export_user):
    check_application_permission(export_application, test_export_user, "export")


def test_application_missing_exporter_access_permission(export_application, test_export_user):
    with pytest.raises(PermissionDenied):
        group = Group.objects.get(name=Perms.obj.exporter.get_group_name())
        test_export_user.groups.remove(group)

        check_application_permission(export_application, test_export_user, "export")


def test_export_application_missing_is_contact_of_exporter_permission(
    export_application, test_export_user
):
    with pytest.raises(PermissionDenied):
        remove_perm("web.is_contact_of_exporter", test_export_user, export_application.exporter)
        check_application_permission(export_application, test_export_user, "export")


# Agent for exporter tests
def test_export_agent_application_valid(agent_export_application, test_agent_export_user):
    check_application_permission(agent_export_application, test_agent_export_user, "export")


def test_export_agent_application_missing_exporter_access_permission(
    agent_export_application, test_agent_export_user
):
    with pytest.raises(PermissionDenied):
        group = Group.objects.get(name=Perms.obj.exporter.get_group_name())
        test_agent_export_user.groups.remove(group)

        check_application_permission(agent_export_application, test_agent_export_user, "export")


def test_export_agent_application_missing_is_contact_of_exporter_permission(
    agent_export_application, test_agent_export_user
):
    with pytest.raises(PermissionDenied):
        remove_perm(
            "web.is_agent_of_exporter",
            test_agent_export_user,
            agent_export_application.exporter,
        )
        check_application_permission(agent_export_application, test_agent_export_user, "export")


# Access Tests
def test_access_application_valid(
    import_access_request_application, export_access_request_application, test_access_user
):
    check_application_permission(import_access_request_application, test_access_user, "access")
    check_application_permission(export_access_request_application, test_access_user, "access")


def test_access_application_denied_for_different_user(
    import_access_request_application, export_access_request_application
):
    another_user = ActiveUserFactory.create()

    with pytest.raises(PermissionDenied):
        check_application_permission(import_access_request_application, another_user, "access")

    with pytest.raises(PermissionDenied):
        check_application_permission(import_access_request_application, another_user, "access")


# Invalid case_type test
def test_invalid_case_type(import_application, test_import_user):
    with pytest.raises(PermissionDenied):
        check_application_permission(import_application, test_import_user, "something-invalid")
