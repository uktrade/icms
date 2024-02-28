import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command
from django.test import override_settings

from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
    DATA_TYPE_XML,
)
from data_migration.management.commands.types import QueryModel
from data_migration.utils import xml_parser
from web import models as web
from web.permissions import (
    ConstabularyObjectPermissions,
    ExporterObjectPermissions,
    ImporterObjectPermissions,
)

from . import utils

user_data_source_target = {
    "user": [
        (dm.User, web.User),
        (dm.PhoneNumber, web.PhoneNumber),
        (dm.Email, web.Email),
        (dm.Constabulary, web.Constabulary),
        (dm.Importer, web.Importer),
        (dm.Exporter, web.Exporter),
        (dm.Office, web.Office),
        (dm.Process, web.Process),
        (dm.AccessRequest, web.AccessRequest),
        (dm.ImporterAccessRequest, web.ImporterAccessRequest),
        (dm.ExporterAccessRequest, web.ExporterAccessRequest),
        (dm.FurtherInformationRequest, web.FurtherInformationRequest),
        (dm.ApprovalRequest, web.ApprovalRequest),
        (dm.ImporterApprovalRequest, web.ImporterApprovalRequest),
        (dm.ExporterApprovalRequest, web.ExporterApprovalRequest),
    ],
}


@pytest.mark.django_db
@mock.patch.dict(
    DATA_TYPE_QUERY_MODEL,
    {
        "reference": [],
        "user": [
            QueryModel(queries.users, "users", dm.User),
            QueryModel(queries.constabularies, "constabularies", dm.Constabulary),
            QueryModel(queries.importers, "importers", dm.Importer),
            QueryModel(queries.importer_offices, "importer_offices", dm.Office),
            QueryModel(queries.exporters, "exporters", dm.Exporter),
            QueryModel(queries.exporter_offices, "exporter_offices", dm.Office),
            QueryModel(queries.access_requests, "access_requests", dm.AccessRequest),
        ],
    },
)
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, user_data_source_target)
@mock.patch.dict(
    DATA_TYPE_M2M,
    {
        "user": [
            (dm.Office, web.Importer, "offices"),
            (dm.Office, web.Exporter, "offices"),
            (dm.FurtherInformationRequest, web.AccessRequest, "further_information_requests"),
        ],
    },
)
@mock.patch.dict(
    DATA_TYPE_XML,
    {
        "user": [
            xml_parser.PersonalEmailAddressParser,
            xml_parser.AlternativeEmailAddressParser,
            xml_parser.PhoneNumberParser,
            xml_parser.ApprovalRequestParser,
            xml_parser.AccessFIRParser,
        ],
    },
)
@mock.patch.object(oracledb, "connect")
@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "web.auth.fox_hasher.FOXPBKDF2SHA1Hasher",
    ]
)
def test_import_user_data(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()

    call_command("export_from_v1", "--skip_ia", "--skip_export", "--skip_ref", "--skip_file")
    call_command("extract_v1_xml", "--skip_ia", "--skip_export", "--skip_ref", "--skip_file")
    call_command("import_v1_data", "--skip_ia", "--skip_export", "--skip_ref", "--skip_file")

    assert web.User.objects.filter(groups__isnull=False).count() == 0

    call_command("create_icms_groups")
    call_command("post_migration")

    assert web.User.objects.count() == 14

    # Check User Data

    users = web.User.objects.filter(pk__in=[2, 3]).order_by("pk")
    u1: web.User = users[0]
    u2: web.User = users[1]

    assert u1.username == "ilb_case_officer@example.com"  # /PS-IGNORE
    assert u1.first_name == "ILB"
    assert u1.last_name == "Case-Officer"
    assert u1.email == "ilb_case_officer@example.com"  # /PS-IGNORE
    assert u1.check_password("password") is True
    assert u1.title == "Mr"
    assert u1.organisation == "Org"
    assert u1.department == "Dept"
    assert u1.job_title == "IT"
    assert u1.last_login == dt.datetime(2022, 11, 1, 12, 32, tzinfo=dt.UTC)
    assert u1.icms_v1_user
    assert u1.phone_numbers.count() == 2

    pn1, pn2 = u1.phone_numbers.order_by("pk")
    assert pn1.phone == "12345678"
    assert pn1.type == "HOME"
    assert pn1.comment == "My Home"
    assert pn2.phone == "+212345678"
    assert pn2.type == "MOBILE"
    assert pn2.comment is None

    assert u1.emails.count() == 5
    pe1, pe2, pe3, pe4, pe5 = u1.emails.order_by("pk")

    # Personal Emails

    assert pe1.email == "test_a"
    assert pe1.type == "HOME"
    assert pe1.portal_notifications is True
    assert pe1.is_primary is True
    assert pe1.comment == "A COMMENT"

    assert pe2.email == "test_b"
    assert pe2.type == "WORK"
    assert pe2.portal_notifications is True
    assert pe2.comment is None

    assert pe3.email == "test_c"
    assert pe3.type == "HOME"
    assert pe3.portal_notifications is False
    assert pe3.is_primary is False
    assert pe3.comment is None

    # Alternative Emails

    assert pe4.email == "test_d"
    assert pe4.type == "HOME"
    assert pe4.portal_notifications is True
    assert pe4.is_primary is False
    assert pe4.comment == "A COMMENT"

    assert pe5.email == "test_e"
    assert pe5.type == "WORK"
    assert pe5.portal_notifications is False
    assert pe5.is_primary is False
    assert pe5.comment is None

    assert u2.check_password("password123") is True
    assert u2.phone_numbers.count() == 0
    assert u2.emails.count() == 0
    assert u2.last_login == dt.datetime(2022, 11, 1, 12, 32, tzinfo=dt.UTC)
    assert u2.icms_v1_user

    # Check Access Request / Approval Request

    ar1, ar2, ar3, ar4 = web.AccessRequest.objects.order_by("pk")

    assert web.UniqueReference.objects.get(prefix="IAR", year=None, reference=1)
    assert ar1.process_ptr.process_type == "ImporterAccessRequest"
    assert ar1.process_ptr.tasks.count() == 1
    assert ar1.reference == "IAR/0001"
    assert ar1.status == "SUBMITTED"
    assert ar1.organisation_name == "Test Org"
    assert ar1.organisation_address == "Test Address"
    assert ar1.agent_name is None
    assert ar1.agent_address == ""
    assert ar1.response is None
    assert ar1.response_reason == ""
    assert ar1.importeraccessrequest.request_type == "MAIN_IMPORTER_ACCESS"
    assert ar1.importeraccessrequest.link_id == 2
    assert ar1.further_information_requests.count() == 0
    assert ar1.approval_requests.count() == 0
    assert ar1.created == dt.datetime(2022, 10, 14, 7, 24, tzinfo=dt.UTC)
    assert ar1.submit_datetime == dt.datetime(2022, 10, 14, 7, 24, tzinfo=dt.UTC)
    assert ar1.last_update_datetime == dt.datetime(2022, 10, 14, 7, 24, tzinfo=dt.UTC)
    assert ar1.closed_datetime is None

    assert web.UniqueReference.objects.get(prefix="IAR", year=None, reference=2)
    assert ar2.process_ptr.process_type == "ImporterAccessRequest"
    assert ar2.process_ptr.tasks.count() == 0
    assert ar2.reference == "IAR/0002"
    assert ar2.status == "CLOSED"
    assert ar2.agent_name == "Test Name"
    assert ar2.agent_address == "Test Address"
    assert ar2.request_reason == "Test Reason"
    assert ar2.response == "APPROVED"
    assert ar2.response_reason == "Test Reason"
    assert ar2.importeraccessrequest.request_type == "AGENT_IMPORTER_ACCESS"
    assert ar2.importeraccessrequest.link_id == 3
    assert ar2.further_information_requests.count() == 0
    assert ar2.approval_requests.count() == 1
    assert ar2.created == dt.datetime(2022, 11, 14, 8, 47, tzinfo=dt.UTC)
    assert ar2.submit_datetime == dt.datetime(2022, 11, 14, 8, 47, tzinfo=dt.UTC)
    assert ar2.last_update_datetime == dt.datetime(2022, 11, 14, 8, 48, tzinfo=dt.UTC)
    assert ar2.closed_datetime == dt.datetime(2022, 11, 14, 8, 48, tzinfo=dt.UTC)

    ar2_ar = ar2.approval_requests.first()
    assert ar2_ar.process_ptr.process_type == "ImporterApprovalRequest"
    assert ar2_ar.status == "COMPLETED"
    assert ar2_ar.response == "APPROVE"
    assert ar2_ar.response_reason == "Test Reason"
    assert ar2_ar.importerapprovalrequest.pk == ar2_ar.pk
    assert ar2_ar.request_date == dt.datetime(2022, 11, 14, 14, 55, 14, tzinfo=dt.UTC)

    assert web.UniqueReference.objects.get(prefix="EAR", year=None, reference=3)
    assert ar3.process_ptr.process_type == "ExporterAccessRequest"
    assert ar3.process_ptr.tasks.count() == 0
    assert ar3.reference == "EAR/0003"
    assert ar3.exporteraccessrequest.request_type == "MAIN_EXPORTER_ACCESS"
    assert ar3.exporteraccessrequest.link_id == 2
    assert ar3.further_information_requests.count() == 1
    assert ar3.approval_requests.count() == 0
    assert ar3.created == dt.datetime(2022, 11, 14, 10, 52, tzinfo=dt.UTC)

    assert web.UniqueReference.objects.get(prefix="EAR", year=None, reference=4)
    assert ar4.process_ptr.process_type == "ExporterAccessRequest"
    assert ar4.process_ptr.tasks.count() == 0
    assert ar4.reference == "EAR/0004"
    assert ar4.exporteraccessrequest.request_type == "AGENT_EXPORTER_ACCESS"
    assert ar4.exporteraccessrequest.link_id == 3
    assert ar4.further_information_requests.count() == 0
    assert ar4.approval_requests.count() == 1
    assert ar4.created == dt.datetime(2022, 11, 14, 10, 52, tzinfo=dt.UTC)

    ar4_ar = ar4.approval_requests.first()
    assert ar4_ar.process_ptr.process_type == "ExporterApprovalRequest"
    assert ar4_ar.status == "COMPLETED"
    assert ar4_ar.response == "APPROVE"
    assert ar4_ar.response_reason == "Test Reason"
    assert ar4_ar.exporterapprovalrequest.pk == ar4_ar.pk

    # Check Groups / Permissions

    assert web.User.objects.filter(groups__isnull=False).count() == 13
    assert (
        web.User.objects.get(groups__name="ILB Case Officer").username
        == "ilb_case_officer@example.com"  # /PS-IGNORE
    )
    assert (
        web.User.objects.get(groups__name="Home Office Case Officer").username
        == "home_office@example.com"  # /PS-IGNORE
    )
    assert (
        web.User.objects.get(groups__name="NCA Case Officer").username
        == "nca@example.com"  # /PS-IGNORE
    )
    assert (
        web.User.objects.get(groups__name="Import Search User").username
        == "import_search_user@example.com"  # /PS-IGNORE
    )

    constabulary_user = web.User.objects.get(groups__name="Constabulary Contact")
    constabulary = web.Constabulary.objects.get(id=1)
    COP = ConstabularyObjectPermissions

    assert constabulary_user.username == "constabulary_contact@example.com"  # /PS-IGNORE
    assert constabulary_user.has_perm(COP.verified_fa_authority_editor, constabulary) is True
    assert web.User.objects.filter(groups__name="Importer User").count() == 4

    IOP = ImporterObjectPermissions
    importer_org = web.Importer.objects.get(id=2)
    importer_agent_org = web.Importer.objects.get(id=3)

    user = web.User.objects.get(username="importer_viewer@example.com")  # /PS-IGNORE
    assert user.has_perm(IOP.view, importer_org) is True
    assert user.has_perm(IOP.edit, importer_org) is False
    assert user.has_perm(IOP.manage_contacts_and_agents, importer_org) is False
    assert user.has_perm(IOP.is_agent, importer_org) is False

    user = web.User.objects.get(username="importer_editor@example.com")  # /PS-IGNORE
    assert user.has_perm(IOP.view, importer_org) is False
    assert user.has_perm(IOP.edit, importer_org) is True
    assert user.has_perm(IOP.manage_contacts_and_agents, importer_org) is True
    assert user.has_perm(IOP.is_agent, importer_org) is False

    user = web.User.objects.get(username="importer_agent_viewer@example.com")  # /PS-IGNORE
    assert user.has_perm(IOP.view, importer_org) is False
    assert user.has_perm(IOP.edit, importer_org) is False
    assert user.has_perm(IOP.manage_contacts_and_agents, importer_org) is False
    assert user.has_perm(IOP.is_agent, importer_org) is True
    assert user.has_perm(IOP.view, importer_agent_org) is True
    assert user.has_perm(IOP.edit, importer_agent_org) is False
    assert user.has_perm(IOP.manage_contacts_and_agents, importer_agent_org) is False

    user = web.User.objects.get(username="importer_agent_editor@example.com")  # /PS-IGNORE
    assert user.has_perm(IOP.view, importer_org) is False
    assert user.has_perm(IOP.edit, importer_org) is False
    assert user.has_perm(IOP.manage_contacts_and_agents, importer_org) is False
    assert user.has_perm(IOP.is_agent, importer_org) is True
    assert user.has_perm(IOP.view, importer_agent_org) is True
    assert user.has_perm(IOP.edit, importer_agent_org) is True
    assert user.has_perm(IOP.manage_contacts_and_agents, importer_agent_org) is False

    assert web.User.objects.filter(groups__name="Exporter User").count() == 4

    EOP = ExporterObjectPermissions
    exporter_org = web.Exporter.objects.get(id=1)
    exporter_agent_org = web.Exporter.objects.get(id=2)

    user = web.User.objects.get(username="exporter_viewer@example.com")  # /PS-IGNORE
    assert user.has_perm(EOP.view, exporter_org) is True
    assert user.has_perm(EOP.edit, exporter_org) is False
    assert user.has_perm(EOP.manage_contacts_and_agents, exporter_org) is False
    assert user.has_perm(EOP.is_agent, exporter_org) is False

    user = web.User.objects.get(username="exporter_editor@example.com")  # /PS-IGNORE
    assert user.has_perm(EOP.view, exporter_org) is False
    assert user.has_perm(EOP.edit, exporter_org) is True
    assert user.has_perm(EOP.manage_contacts_and_agents, exporter_org) is True
    assert user.has_perm(EOP.is_agent, exporter_org) is False

    user = web.User.objects.get(username="exporter_agent_viewer@example.com")  # /PS-IGNORE
    assert user.has_perm(EOP.view, exporter_org) is False
    assert user.has_perm(EOP.edit, exporter_org) is False
    assert user.has_perm(EOP.manage_contacts_and_agents, exporter_org) is False
    assert user.has_perm(EOP.is_agent, exporter_org) is True
    assert user.has_perm(EOP.view, exporter_agent_org) is True
    assert user.has_perm(EOP.edit, exporter_agent_org) is False
    assert user.has_perm(EOP.manage_contacts_and_agents, exporter_agent_org) is False

    user = web.User.objects.get(username="exporter_agent_editor@example.com")  # /PS-IGNORE
    assert user.has_perm(EOP.view, exporter_org) is False
    assert user.has_perm(EOP.edit, exporter_org) is False
    assert user.has_perm(EOP.manage_contacts_and_agents, exporter_org) is False
    assert user.has_perm(EOP.is_agent, exporter_org) is True
    assert user.has_perm(EOP.view, exporter_agent_org) is True
    assert user.has_perm(EOP.edit, exporter_agent_org) is True
    assert user.has_perm(EOP.manage_contacts_and_agents, exporter_agent_org) is False

    # Check users that are excluded from V2 migration
    assert dm.User.objects.filter(id=15).exists()
    assert not web.User.objects.filter(id=15).exists()

    assert dm.Email.objects.filter(email="test_a_excluded").exists()
    assert not web.Email.objects.filter(email="test_a_excluded").exists()

    assert dm.PhoneNumber.objects.filter(phone="999").exists()
    assert not web.PhoneNumber.objects.filter(phone="999").exists()

    assert dm.Importer.objects.filter(pk=4).exists()
    assert not web.Importer.objects.filter(pk=4).exists()
