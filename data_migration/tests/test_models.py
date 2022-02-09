import pytest

from data_migration.models import MigrationBase

from .factory import CountryFactory, CountryGroupFactory, ImportApplicationTypeFactory


@pytest.mark.django_db
def test_active_status_data_export():
    data = {"id": 1, "name": "test", "status": "ACTIVE"}
    result = MigrationBase.data_export(data)
    assert len(result.keys()) == 3
    assert result["id"] == 1
    assert result["name"] == "test"
    assert result["is_active"] is True


@pytest.mark.django_db
def test_inactive_status_data_export():
    data = {"id": 1, "name": "test", "status": "INACTIVE"}
    result = MigrationBase.data_export(data)
    assert len(result.keys()) == 3
    assert result["is_active"] is False


@pytest.mark.django_db
def test_country_get_values():
    country = CountryFactory()
    values = country.get_values()
    expected = ["commission_code", "hmrc_code", "id", "name", "status", "type"]
    assert sorted(values) == expected


@pytest.mark.django_db
def test_country_group_get_values():
    country_group = CountryGroupFactory()
    values = country_group.get_values()
    assert sorted(values) == ["comments", "id", "name"]


@pytest.mark.django_db
def test_country_data_export():
    country = CountryFactory(status="ACTIVE")
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
    iat = ImportApplicationTypeFactory()
    result = iat.get_related()
    expected = [
        "commodity_type",
        "consignment_country_group",
        "default_commodity_group",
        "master_country_group",
        "origin_country_group",
    ]

    assert result == expected


@pytest.mark.django_db
def test_import_application_type_values():
    iat = ImportApplicationTypeFactory()
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
    iat = ImportApplicationTypeFactory(sigl_flag="true", endorsements_flag="false")
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
