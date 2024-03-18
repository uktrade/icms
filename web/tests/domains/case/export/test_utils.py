import io

import pytest
from django.core.files.base import File

from web.domains.case.export.utils import (
    CustomError,
    copy_export_application,
    process_products_file,
)
from web.domains.case.shared import ImpExpStatus
from web.models import CFSSchedule
from web.tests.domains.legislation.factory import ProductLegislationFactory
from web.utils.spreadsheet import XlsxSheetConfig, generate_xlsx_file


def create_dummy_config(is_biocidal: bool = False) -> XlsxSheetConfig:
    config = XlsxSheetConfig()
    config.sheet_name = "CFS Products"

    if is_biocidal:
        config.header.data = [
            "Product Name",
            "Product Type Numbers (CSV)",
            "Active Ingredient Name",
            "Active Ingredient CAS Number",
        ]
        config.rows = [
            ["Product 1", "1,2,3", "Ingredient 1", "111-11-1"],
            ["Product 1", "1,2,3", "Ingredient 2", "111-11-2"],
            ["Product 2", "4,5,6", "Ingredient 3", "111-11-3"],
            ["Product 3", "7", "Ingredient 4", "111-11-4"],
        ]

    else:
        config.header.data = ["Product Name"]
        config.rows = [
            ["Product 1"],
            ["Product 2"],
            ["Product 3"],
        ]

    return config


def create_dummy_xlsx_file(config: XlsxSheetConfig) -> File:
    xlsx_data = generate_xlsx_file([config])
    xlsx_file = File(io.BytesIO(xlsx_data))

    return xlsx_file


def create_schedule(app, is_biocidal: bool = False):
    legislation = ProductLegislationFactory()
    legislation.is_biocidal = is_biocidal
    legislation.save()

    schedule = CFSSchedule.objects.create(application=app, created_by=app.last_updated_by)
    schedule.legislations.add(legislation)

    return schedule


@pytest.mark.django_db
@pytest.mark.parametrize("is_biocidal", [False, True])
def test_process_products_file(cfs_app_submitted, is_biocidal):
    schedule = create_schedule(cfs_app_submitted, is_biocidal)
    config = create_dummy_config(is_biocidal=is_biocidal)
    xlsx_file = create_dummy_xlsx_file(config)
    count = process_products_file(xlsx_file, schedule)

    assert count == 3
    assert schedule.products.count() == 3
    assert schedule.products.filter(product_name="Product 1").count() == 1

    if is_biocidal:
        product_1 = schedule.products.get(product_name="Product 1")
        assert product_1.active_ingredients.count() == 2
        assert product_1.product_type_numbers.count() == 3


@pytest.mark.django_db
def test_multiple_chunks_invalid(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted)
    config = create_dummy_config()
    xlsx_file = create_dummy_xlsx_file(config)
    xlsx_file.DEFAULT_CHUNK_SIZE = 5000

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "File too large to process" in str(e.value)


@pytest.mark.django_db
def test_sheet_name_invalid(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted)
    config = create_dummy_config()
    config.sheet_name = "Sheet 1"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Cannot find sheet with name 'CFS Products' in file" in str(e.value)


@pytest.mark.django_db
@pytest.mark.parametrize("is_biocidal", [False, True])
def test_invalid_header(cfs_app_submitted, is_biocidal):
    schedule = create_schedule(cfs_app_submitted, is_biocidal)
    config = create_dummy_config(is_biocidal is False)
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Spreadsheet header does not match the template header" in str(e.value)


@pytest.mark.django_db
@pytest.mark.parametrize("is_biocidal", [False, True])
def test_invalid_row_width(cfs_app_submitted, is_biocidal):
    schedule = create_schedule(cfs_app_submitted, is_biocidal)
    config = create_dummy_config(is_biocidal)
    config.rows.append(["Product 4", "8", "Ingredient 5", "111-11-5", "Extra"])

    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Number of columns with data do not match the number of columns in the header" in str(
        e.value
    )


@pytest.mark.django_db
def test_missing_product_name(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted)
    config = create_dummy_config()
    config.rows[1][0] = None
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Data missing in column 'Product Name' - line 3" in str(e.value)


@pytest.mark.django_db
def test_invalid_product_type_number(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted, is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][1] = "a"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Product type number 'a' for product 'Product 1' is not a number - line 3" in str(
        e.value
    )


@pytest.mark.django_db
def test_missing_ingredient_name(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted, is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][2] = None
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Ingredient name missing - line 3" in str(e.value)


@pytest.mark.django_db
def test_missing_cas_number(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted, is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][3] = None
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "CAS number missing - line 3" in str(e.value)


@pytest.mark.django_db
def test_duplicate_ingredient_name(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted, is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][2] = "Ingredient 1"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Ingredient name 'Ingredient 1' duplicated for product 'Product 1' - line 3" in str(
        e.value
    )


@pytest.mark.django_db
def test_duplicate_cas_number(cfs_app_submitted):
    schedule = create_schedule(cfs_app_submitted, is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][3] = "111-11-1"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "CAS number '111-11-1' duplicated for product 'Product 1' - line 3" in str(e.value)


def test_copy_cfs_application(
    cfs_app_submitted, exporter_two, exporter_two_office, exporter_two_contact
):
    new_app = copy_export_application(
        cfs_app_submitted,
        exporter=exporter_two,
        exporter_office=exporter_two_office,
        agent=None,
        agent_office=None,
        created_by=exporter_two_contact,
    )

    assert not new_app.reference
    assert new_app.status == ImpExpStatus.IN_PROGRESS
    _assert_many_to_many_equal(cfs_app_submitted.countries, new_app.countries)

    assert cfs_app_submitted.schedules.count() == new_app.schedules.count()

    for existing, new in zip(cfs_app_submitted.schedules.all(), new_app.schedules.all()):
        _assert_many_to_many_equal(existing.legislations, new.legislations)

        for field in [
            "exporter_status",
            "brand_name_holder",
            "biocidal_claim",
            "product_eligibility",
            "goods_placed_on_uk_market",
            "goods_export_only",
            "any_raw_materials",
            "final_product_end_use",
            "country_of_manufacture",
            "schedule_statements_accordance_with_standards",
            "schedule_statements_is_responsible_person",
            "manufacturer_name",
            "manufacturer_address_entry_type",
            "manufacturer_postcode",
            "manufacturer_address",
        ]:
            _assert_field_equal(existing, new, field)

        for existing_product, new_product in zip(existing.products.all(), new.products.all()):
            _assert_field_equal(existing_product, new_product, "product_name")
            assert (
                existing_product.product_type_numbers.count()
                == new_product.product_type_numbers.count()
            )
            assert (
                existing_product.active_ingredients.count()
                == new_product.active_ingredients.count()
            )


def test_copy_com_application(
    com_app_submitted, exporter_two, exporter_two_office, exporter_two_contact
):
    new_app = copy_export_application(
        com_app_submitted,
        exporter=exporter_two,
        exporter_office=exporter_two_office,
        agent=None,
        agent_office=None,
        created_by=exporter_two_contact,
    )

    assert not new_app.reference
    assert new_app.status == ImpExpStatus.IN_PROGRESS
    _assert_many_to_many_equal(com_app_submitted.countries, new_app.countries)

    for field in [
        "is_pesticide_on_free_sale_uk",
        "is_manufacturer",
        "product_name",
        "chemical_name",
        "manufacturing_process",
    ]:
        _assert_field_equal(com_app_submitted, new_app, field)


def test_copy_gmp_application(
    gmp_app_submitted, exporter_two, exporter_two_office, exporter_two_contact
):
    new_app = copy_export_application(
        gmp_app_submitted,
        exporter=exporter_two,
        exporter_office=exporter_two_office,
        agent=None,
        agent_office=None,
        created_by=exporter_two_contact,
    )

    assert not new_app.reference
    assert new_app.status == ImpExpStatus.IN_PROGRESS
    _assert_many_to_many_equal(gmp_app_submitted.countries, new_app.countries)

    for field in [
        "brand_name",
        "is_responsible_person",
        "responsible_person_name",
        "responsible_person_address_entry_type",
        "responsible_person_postcode",
        "responsible_person_address",
        "responsible_person_country",
        "is_manufacturer",
        "manufacturer_name",
        "manufacturer_address_entry_type",
        "manufacturer_postcode",
        "manufacturer_address",
        "manufacturer_country",
        "gmp_certificate_issued",
        "auditor_accredited",
        "auditor_certified",
    ]:
        _assert_field_equal(gmp_app_submitted, new_app, field)


def _assert_field_equal(existing, new, field_name):
    assert getattr(existing, field_name) == getattr(new, field_name)


def _assert_many_to_many_equal(existing_m2m, new_m2m):
    existing_pks = existing_m2m.values_list("pk", flat=True)
    new_pks = new_m2m.values_list("pk", flat=True)

    assert list(existing_pks) == list(new_pks)
