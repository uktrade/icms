import pytest

from data_migration import models as dm

from . import factory


@pytest.mark.django_db
def test_country_get_values():
    country = factory.CountryFactory()
    values = country.get_values()
    expected = ["commission_code", "hmrc_code", "id", "is_active", "name", "type"]
    assert sorted(values) == expected


@pytest.mark.django_db
def test_country_group_get_values():
    country_group = factory.CountryGroupFactory()
    values = country_group.get_values()
    assert sorted(values) == ["comments", "id", "name"]


@pytest.mark.django_db
def test_country_data_export():
    country = factory.CountryFactory(is_active=True)
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
def test_import_application_type_values():
    iat = factory.ImportApplicationTypeFactory()
    result = iat.get_values()
    expected = [
        "case_checklist_flag",
        "category_flag",
        "chief_category_prefix",
        "chief_flag",
        "chief_licence_prefix",
        "cover_letter_flag",
        "cover_letter_schedule_flag",
        "default_commodity_desc",
        "default_licence_length_months",
        "electronic_licence_flag",
        "exp_cert_upload_flag",
        "guidance_file_url",
        "id",
        "importer_printable",
        "is_active",
        "licence_category_description",
        "licence_type_code",
        "multiple_commodities_flag",
        "name",
        "paper_licence_flag",
        "quantity_unlimited_flag",
        "sigl_category_prefix",
        "sigl_flag",
        "sub_type",
        "supporting_docs_upload_flag",
        "type",
        "unit_list_csv",
        "usage_auto_category_desc_flag",
    ]

    assert sorted(result) == expected


@pytest.mark.django_db
def test_import_application_type_data_export():
    iat = factory.ImportApplicationTypeFactory(sigl_flag="true")
    data_dict = iat.__dict__
    data_dict.pop("_state")

    for field in iat.get_excludes():
        data_dict.pop(field)

    for field in iat.get_includes():
        data_dict[field] = 1234

    result = iat.data_export(data_dict)
    assert len(result.keys()) == 28
    assert result["sigl_flag"] is True


@pytest.mark.django_db
def test_import_application_get_data_export():
    process = factory.ProcessFactory(ima_id=1)
    ia = factory.ImportApplicationFactory(ima=process)
    data = {k: None for k in ia.get_values()}
    data["legacy_case_flag"] = "true"
    data["licence_extended_flag"] = "false"
    data["variation_no"] = 0
    result = ia.data_export(data)

    assert result["legacy_case_flag"] is True
    assert result["licence_extended_flag"] is False

    expected = [
        "agent_id",
        "applicant_reference",
        "application_type_id",
        "case_owner_id",
        "chief_usage_status",
        "commodity_group_id",
        "consignment_country_id",
        "contact_id",
        "cover_letter_text",
        "create_datetime",
        "created_by_id",
        "decision",
        "id",
        "imi_submit_datetime",
        "imi_submitted_by_id",
        "importer_id",
        "last_update_datetime",
        "last_updated_by_id",
        "legacy_case_flag",
        "licence_extended_flag",
        "origin_country_id",
        "reference",
        "refuse_reason",
        "status",
        "submit_datetime",
        "submitted_by_id",
        "variation_decision",
        "variation_refuse_reason",
    ]
    assert sorted(result.keys()) == expected


@pytest.mark.django_db
def test_wood_application_get_data_export():
    process = factory.ProcessFactory(ima_id=1)
    ia = factory.ImportApplicationFactory(ima=process)
    wood = dm.WoodQuotaApplication.objects.create(imad=ia)
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
