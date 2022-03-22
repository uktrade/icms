from datetime import datetime

import pytest

from data_migration import models as dm

from . import factory, xml_data


@pytest.mark.django_db
def test_active_status_data_export():
    data = {"id": 1, "name": "test", "status": "ACTIVE"}
    result = dm.MigrationBase.data_export(data)
    assert len(result.keys()) == 3
    assert result["id"] == 1
    assert result["name"] == "test"
    assert result["is_active"] is True


@pytest.mark.django_db
def test_inactive_status_data_export():
    data = {"id": 1, "name": "test", "status": "INACTIVE"}
    result = dm.MigrationBase.data_export(data)
    assert len(result.keys()) == 3
    assert result["is_active"] is False


@pytest.mark.django_db
def test_country_get_values():
    country = factory.CountryFactory()
    values = country.get_values()
    expected = ["commission_code", "hmrc_code", "id", "name", "status", "type"]
    assert sorted(values) == expected


@pytest.mark.django_db
def test_country_group_get_values():
    country_group = factory.CountryGroupFactory()
    values = country_group.get_values()
    assert sorted(values) == ["comments", "id", "name"]


@pytest.mark.django_db
def test_country_data_export():
    country = factory.CountryFactory(status="ACTIVE")
    data_dict = country.__dict__
    data_dict.pop("_state")
    data = country.data_export(data_dict)
    assert len(data.keys()) == 6
    assert data["id"] == country.id
    assert data["name"] == country.name
    assert data["is_active"] is True
    assert data["type"] == country.type
    assert data["commission_code"] == country.commission_code
    assert data["hmrc_code"] == country.hmrc_code


@pytest.mark.django_db
def test_import_application_type_related():
    iat = factory.ImportApplicationTypeFactory()
    result = iat.get_related()
    expected = [
        "commodity_type",
        "consignment_country_group",
        "default_commodity_group",
        "master_country_group",
        "origin_country_group",
    ]

    assert sorted(result) == expected


@pytest.mark.django_db
def test_import_application_type_values():
    iat = factory.ImportApplicationTypeFactory()
    result = iat.get_values()
    expected = [
        "case_checklist_flag",
        "category_flag",
        "chief_category_prefix",
        "chief_flag",
        "chief_licence_prefix",
        "commodity_type__id",
        "commodity_type_id",
        "consignment_country_group__id",
        "consignment_country_group_id",
        "cover_letter_flag",
        "cover_letter_schedule_flag",
        "default_commodity_desc",
        "default_commodity_group__id",
        "default_commodity_group_id",
        "default_licence_length_months",
        "electronic_licence_flag",
        "endorsements_flag",
        "exp_cert_upload_flag",
        "guidance_file_url",
        "id",
        "importer_printable",
        "licence_category_description",
        "licence_type_code",
        "master_country_group__id",
        "master_country_group_id",
        "multiple_commodities_flag",
        "origin_country_group__id",
        "origin_country_group_id",
        "paper_licence_flag",
        "quantity_unlimited_flag",
        "sigl_category_prefix",
        "sigl_flag",
        "status",
        "sub_type",
        "supporting_docs_upload_flag",
        "type",
        "unit_list_csv",
        "usage_auto_category_desc_flag",
    ]

    assert sorted(result) == expected


@pytest.mark.django_db
def test_import_application_type_data_export():
    iat = factory.ImportApplicationTypeFactory(sigl_flag="true", endorsements_flag="false")
    data_dict = iat.__dict__
    data_dict.pop("_state")

    for field in iat.get_excludes():
        data_dict.pop(field)

    for field in iat.get_includes():
        data_dict[field] = 1234

    result = iat.data_export(data_dict)
    assert len(result.keys()) == 33
    assert result["sigl_flag"] is True
    assert result["endorsements_flag"] is False
    assert result["origin_country_group_id"] == 1234
    assert "origin_country_group__id" not in result


@pytest.mark.django_db
def test_import_application_get_data_export():
    process = factory.ProcessFactory(ima_id=1)
    ia = factory.ImportApplicationFactory(ima=process)
    data = {k: None for k in ia.get_values()}
    data["legacy_case_flag"] = "true"
    data["licence_extended_flag"] = "false"
    result = ia.data_export(data)

    assert result["legacy_case_flag"] is True
    assert result["under_appeal_flag"] is False
    assert result["licence_extended_flag"] is False

    assert sorted(result.keys()) == [
        "acknowledged_by_id",
        "acknowledged_datetime",
        "agent_id",
        "agent_office_id",
        "applicant_reference",
        "application_type_id",
        "case_owner_id",
        "chief_usage_status",
        "commodity_group_id",
        "consignment_country_id",
        "contact_id",
        "cover_letter",
        "create_datetime",
        "created_by_id",
        "decision",
        "id",
        "imi_submit_datetime",
        "imi_submitted_by_id",
        "importer_id",
        "importer_office_id",
        "issue_date",
        "last_update_datetime",
        "last_updated_by_id",
        "legacy_case_flag",
        "licence_extended_flag",
        "licence_reference",
        "origin_country_id",
        "process_ptr_id",
        "reference",
        "refuse_reason",
        "status",
        "submit_datetime",
        "submitted_by_id",
        "under_appeal_flag",
        "variation_decision",
        "variation_no",
        "variation_refuse_reason",
    ]


@pytest.mark.django_db
def test_wood_application_get_data_export():
    process = factory.ProcessFactory(ima_id=1)
    ia = factory.ImportApplicationFactory(ima=process)
    wood = factory.WoodQuotaApplicationFactory(imad=ia)
    data = {k: None for k in wood.get_values()}
    result = wood.data_export(data)

    assert sorted(result.keys()) == [
        "additional_comments",
        "commodity_id",
        "exporter_address",
        "exporter_name",
        "exporter_vat_nr",
        "goods_description",
        "goods_qty",
        "goods_unit",
        "id",
        "importapplication_ptr_id",
        "shipping_year",
    ]


def test_oil_application_parse_xml():
    reports = dm.OILSupplementaryReport.parse_xml(
        [(1, xml_data.sr_upload_xml), (2, xml_data.sr_manual_xml)]
    )

    assert len(reports) == 3
    sr1, sr2, sr3 = reports
    assert sr1.transport == "AIR"
    assert sr1.date_received == datetime.strptime("2021-10-14", "%Y-%m-%d").date()
    assert sr1.supplementary_info_id == 1
    assert sr2.transport == "RAIL"
    assert sr2.date_received == datetime.strptime("2021-11-03", "%Y-%m-%d").date()
    assert sr2.supplementary_info_id == 2
    assert sr3.transport is None
    assert sr3.date_received is None
    assert sr3.supplementary_info_id == 2

    firearms = dm.OILSupplementaryReportFirearm.parse_xml(
        [(1, sr1.report_firearms_xml), (2, sr2.report_firearms_xml), (3, sr3.report_firearms_xml)]
    )
    assert len(firearms) == 4
    f1, f2, f3, f4 = firearms
    assert f1.is_upload is True
    assert (f1.is_manual and f1.is_no_firearm) is False
    assert f1.report_id == 1

    assert f2.is_manual is True
    assert (f2.is_upload and f2.is_no_firearm) is False
    assert f2.serial_number == "N/A"
    assert f2.calibre == "6MM"
    assert f2.model == "A gun barrel"
    assert f2.proofing == "no"
    assert f2.report_id == 2

    assert f3.is_manual is True
    assert (f3.is_upload and f3.is_no_firearm) is False
    assert f3.serial_number == "123456"
    assert f3.calibre == ".30"
    assert f3.model == "A gun"
    assert f3.proofing == "yes"
    assert f3.report_id == 2

    assert f4.is_manual is True
    assert (f4.is_upload and f4.is_no_firearm) is False
    assert f4.report_id == 3
