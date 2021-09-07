import io

import pytest
from django.core.files.base import File

from web.domains.case.export.utils import CustomError, process_products_file
from web.tests.domains.case.export.factories import CFSScheduleFactory
from web.tests.domains.legislation.factory import ProductLegislationFactory
from web.utils.spreadsheet import XlsxConfig, generate_xlsx_file


def create_dummy_config(is_biocidal: bool = False) -> XlsxConfig:
    config = XlsxConfig()
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


def create_dummy_xlsx_file(config: XlsxConfig) -> File:
    xlsx_data = generate_xlsx_file(config)
    xlsx_file = File(io.BytesIO(xlsx_data))

    return xlsx_file


def create_schedule(is_biocidal: bool = False):
    legislation = ProductLegislationFactory()
    legislation.is_biocidal = is_biocidal
    legislation.save()

    schedule = CFSScheduleFactory()
    schedule.legislations.add(legislation)

    return schedule


@pytest.mark.django_db
@pytest.mark.parametrize("is_biocidal", [False, True])
def test_process_products_file(is_biocidal):
    schedule = create_schedule(is_biocidal)
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
def test_multiple_chunks_invalid():
    schedule = create_schedule()
    config = create_dummy_config()
    xlsx_file = create_dummy_xlsx_file(config)
    xlsx_file.DEFAULT_CHUNK_SIZE = 5000

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "File too large to process" in str(e.value)


@pytest.mark.django_db
def test_sheet_name_invalid():
    schedule = create_schedule()
    config = create_dummy_config()
    config.sheet_name = "Sheet 1"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Cannot find sheet with name 'CFS Products' in file" in str(e.value)


@pytest.mark.django_db
@pytest.mark.parametrize("is_biocidal", [False, True])
def test_invalid_header(is_biocidal):
    schedule = create_schedule(is_biocidal)
    config = create_dummy_config(is_biocidal is False)
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Spreadsheet header does not match the template header" in str(e.value)


@pytest.mark.django_db
@pytest.mark.parametrize("is_biocidal", [False, True])
def test_invalid_row_width(is_biocidal):
    schedule = create_schedule(is_biocidal)
    config = create_dummy_config(is_biocidal)
    config.rows.append(["Product 4", "8", "Ingredient 5", "111-11-5", "Extra"])

    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Number of columns with data do not match the number of columns in the header" in str(
        e.value
    )


@pytest.mark.django_db
def test_missing_product_name():
    schedule = create_schedule()
    config = create_dummy_config()
    config.rows[1][0] = None
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Data missing in column 'Product Name' - line 3" in str(e.value)


@pytest.mark.django_db
def test_invalid_product_type_number():
    schedule = create_schedule(is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][1] = "a"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Product type number 'a' for product 'Product 1' is not a number - line 3" in str(
        e.value
    )


@pytest.mark.django_db
def test_missing_ingredient_name():
    schedule = create_schedule(is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][2] = None
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Ingredient name missing - line 3" in str(e.value)


@pytest.mark.django_db
def test_missing_cas_number():
    schedule = create_schedule(is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][3] = None
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "CAS number missing - line 3" in str(e.value)


@pytest.mark.django_db
def test_duplicate_ingredient_name():
    schedule = create_schedule(is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][2] = "Ingredient 1"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "Ingredient name 'Ingredient 1' duplicated for product 'Product 1' - line 3" in str(
        e.value
    )


@pytest.mark.django_db
def test_duplicate_cas_number():
    schedule = create_schedule(is_biocidal=True)
    config = create_dummy_config(is_biocidal=True)
    config.rows[1][3] = "111-11-1"
    xlsx_file = create_dummy_xlsx_file(config)

    with pytest.raises(CustomError) as e:
        process_products_file(xlsx_file, schedule)

    assert "CAS number '111-11-1' duplicated for product 'Product 1' - line 3" in str(e.value)
