import io
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from django.core.files.base import File
from django.forms import ModelForm, ValidationError, model_to_dict
from openpyxl import load_workbook

from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSSchedule,
    Exporter,
    Office,
    User,
)
from web.utils.sentry import capture_message
from web.utils.spreadsheet import XlsxSheetConfig, generate_xlsx_file

from .forms import (
    CFSActiveIngredientForm,
    CFSManufacturerDetailsForm,
    CFSProductForm,
    CFSProductTypeForm,
    EditCFScheduleForm,
    EditCFSForm,
    EditCOMForm,
    EditGMPForm,
)


class CustomError(Exception):
    pass


@dataclass
class ProductData:
    product_type_numbers: list[int] = field(default_factory=list)
    ingredient_names: list[str] = field(default_factory=list)
    cas_numbers: list[str] = field(default_factory=list)


def generate_product_template_xlsx(is_biocidal: bool = False) -> bytes:
    """Generates the schedule products xslx template for download"""

    header_data = _get_header(is_biocidal)
    config = XlsxSheetConfig()
    config.header.data = header_data
    config.header.styles = {"bold": True}
    config.column_width = 25
    config.sheet_name = "CFS Products"

    xlsx_data = generate_xlsx_file([config])
    return xlsx_data


def process_products_file(products_file: File, schedule: CFSSchedule) -> int:
    """Processes the uploaded xlsx file and save the products to the schedule.

    Raises an exception on any validation failure.
    Returns the count of the products which were processed.
    """

    is_biocidal = schedule.is_biocidal()

    products_data = _extract_product_data(products_file, is_biocidal)
    product_count = len(products_data)

    for product_name, product_data in products_data.items():
        product = _process_product(schedule, product_name)

        _process_product_type_numbers(product, product_data)
        _process_ingredients(product, product_data)

    return product_count


def _get_header(is_biocidal: bool = False) -> list[str]:
    """Generates the header row for the xlsx file"""

    if is_biocidal:
        return [
            "Product Name",
            "Product Type Numbers (CSV)",
            "Active Ingredient Name",
            "Active Ingredient CAS Number",
        ]

    return ["Product Name"]


def _extract_sheet_header(sheet, is_biocidal: bool = False) -> list[str]:
    """Get the expected header for xlsx and compare it to header in the first row of data"""

    header = _get_header(is_biocidal)
    header_row = [col.strip() if col else "" for col in next(sheet.values)]

    # Check the number of columns with data in xlsx file matches the length of the header
    if "" in header_row:
        raise CustomError(
            "Number of columns with data do not match the number of columns in the header"
        )

    # Check the header in the xlsx file matches the expected template header
    if header != header_row:
        raise CustomError("Spreadsheet header does not match the template header")

    return header


def _extract_product_data(products_file: File, is_biocidal: bool = False) -> dict[str, ProductData]:
    """Iterates over the rows in the products xlsx and extracts the product data from each row.

    Combines product type numbers and ingredients for the each product.
    Returns the data as an OrderedDict.
    """

    if products_file.multiple_chunks():
        # If there is more than one chunk, the file is too big
        raise CustomError("File too large to process")

    data: OrderedDict = OrderedDict()
    chunk = next(products_file.chunks())
    workbook = load_workbook(filename=io.BytesIO(chunk), read_only=True, data_only=True)

    try:
        if "CFS Products" not in workbook.sheetnames:
            raise CustomError("Cannot find sheet with name 'CFS Products' in file")

        sheet = workbook["CFS Products"]
        header = _extract_sheet_header(sheet, is_biocidal)

        for row, row_values in enumerate(sheet.values, start=1):
            # Skip the header row
            if row == 1:
                continue

            # Clean values in row by stripping whitespace
            values = [
                value and str(value).strip() or ""
                for value in row_values  # type:ignore[union-attr]
            ]

            # Create a dict of values using column name
            row_data = dict(zip(header, values))
            row_data["row"] = str(row)

            product_name = row_data.get("Product Name")

            if not product_name:
                raise CustomError(f"Data missing in column 'Product Name' - line {row}")

            product = data.get(product_name, ProductData())

            # There will be only the product name column in the sheet for non biocidal legislation
            if not is_biocidal:
                data[product_name] = product

                continue

            _add_product_type_numbers_to_product_data(row_data, product)
            _add_ingredient_to_product_data(row_data, product)

            data[product_name] = product

        workbook.close()

    except Exception as err:
        # Catch the exception to explicitly close the workbook before raising
        workbook.close()
        raise err

    return data


def _add_product_type_numbers_to_product_data(
    row_data: dict[str, str], product: ProductData
) -> None:
    """Gets and validates product type numbers data from the row and adds to ProductData.

    Appends the product types numbers to ProductData.product_type_numbers.
    """

    data = row_data.get("Product Type Numbers (CSV)", "")
    product_name = row_data["Product Name"]
    row = row_data["row"]

    for val in data.split(","):
        try:
            # Integers are stored as floats in xlsx files
            product_type = int(float(val))

            if product_type not in product.product_type_numbers:
                product.product_type_numbers.append(product_type)

        except ValueError:
            raise CustomError(
                f"Product type number '{val}' for product '{product_name}' is not a number - line {row}"
            )


def _add_ingredient_to_product_data(
    row_data: dict[str, str],
    product: ProductData,
) -> None:
    """Gets and validates ingredient data from the row and adds to ProductData.

    Appends ingredient name to ProductData.ingredient_names.
    Appends cas number to to ProductData.cas_numbers.
    """

    ingredient_name = row_data.get("Active Ingredient Name")
    cas_number = row_data.get("Active Ingredient CAS Number")
    product_name = row_data["Product Name"]
    row = row_data["row"]

    if not ingredient_name:
        raise CustomError(f"Ingredient name missing - line {row}")

    if not cas_number:
        raise CustomError(f"CAS number missing - line {row}")

    if ingredient_name in product.ingredient_names:
        raise CustomError(
            f"Ingredient name '{ingredient_name}' duplicated for product '{product_name}' - line {row}"
        )

    if cas_number in product.cas_numbers:
        raise CustomError(
            f"CAS number '{cas_number}' duplicated for product '{product_name}' - line {row}"
        )

    product.ingredient_names.append(ingredient_name)
    product.cas_numbers.append(cas_number)


def _process_product(schedule: CFSSchedule, product_name: str) -> CFSProduct:
    """Gets existing product or saves new product using CFSProductForm and returns product"""

    existing_product = schedule.products.filter(product_name__iexact=product_name).first()

    if existing_product:
        return existing_product

    form = CFSProductForm(data={"product_name": product_name}, schedule=schedule)

    if not form.is_valid():
        errors = form.errors

        msg = f"Product '{product_name}' has error"

        if "product_name" in errors:
            msg += f" - {errors['product_name'][0]}"

        raise CustomError(msg)

    return form.save()


def _process_product_type_numbers(product: CFSProduct, product_data: ProductData) -> None:
    """Gets product type numbers from ProductData and saves using CFSProductTypeForm"""

    product_type_numbers = product_data.product_type_numbers
    existing_product_type_numbers = product.product_type_numbers.values_list(
        "product_type_number", flat=True
    )
    for product_type_number in product_type_numbers:
        if product_type_number not in existing_product_type_numbers:
            product_type_form = CFSProductTypeForm(
                data={"product_type_number": product_type_number}, product=product
            )

            if not product_type_form.is_valid():
                errors = product_type_form.errors
                msg = f"product type number '{product_type_number}'"

                if "product_type_number" in errors:
                    msg += f" - {errors['product_type_number'][0]}"

                raise CustomError(f"Product '{product.product_name} has error with {msg}")

            product_type_form.save()


def _process_ingredients(product: CFSProduct, product_data: ProductData) -> None:
    """Gets ingredeient data from ProductData and saves using CFSActiveIngredientForm"""

    ingredient_names = product_data.ingredient_names
    cas_numbers = product_data.cas_numbers

    # ingredient_names and cas_numbers are both appended to for each row of data
    # the index for each ingredient will be the same in each list
    ingredient_data = zip(ingredient_names, cas_numbers)

    for ingredient in ingredient_data:
        name, cas_number = ingredient

        ingredient_form = CFSActiveIngredientForm(
            data={"name": name, "cas_number": cas_number}, product=product
        )

        if not ingredient_form.is_valid():
            errors = ingredient_form.errors

            if "name" in errors:
                msg = f"active ingredient name '{name}' - {errors['name'][0]}"
            elif "cas_number" in errors:
                msg = f"CAS number '{cas_number}' - {errors['cas_number'][0]}"
            else:
                msg = f"active ingredient name '{name}' CAS number '{cas_number}'"

            raise CustomError(f"Product '{product.product_name}' has error with {msg}")

        ingredient_form.save()


def copy_export_application(
    existing_app: (
        CertificateOfFreeSaleApplication
        | CertificateOfManufactureApplication
        | CertificateOfGoodManufacturingPracticeApplication
    ),
    exporter: Exporter,
    exporter_office: Office,
    agent: Exporter | None,
    agent_office: Office | None,
    created_by: User,
) -> (
    CertificateOfFreeSaleApplication
    | CertificateOfManufactureApplication
    | CertificateOfGoodManufacturingPracticeApplication
):
    """Create a new export application from an existing one."""

    match existing_app:
        case CertificateOfFreeSaleApplication():
            model_cls = CertificateOfFreeSaleApplication
            copy_app_data = copy_cfs_data

        case CertificateOfManufactureApplication():
            model_cls = CertificateOfManufactureApplication
            copy_app_data = copy_com_data

        case CertificateOfGoodManufacturingPracticeApplication():
            model_cls = CertificateOfGoodManufacturingPracticeApplication
            copy_app_data = copy_gmp_data

        case _:
            raise ValueError(f"Can't create application for: {existing_app}")

    # Create the new model with basic application data.
    new_app = model_cls.objects.create(
        exporter=exporter,
        exporter_office=exporter_office,
        agent=agent,
        agent_office=agent_office,
        process_type=existing_app.process_type,
        application_type=existing_app.application_type,
        created_by=created_by,
        last_updated_by=created_by,
    )

    # Common model fields to exclude when copying.
    # Most if not all of these fields are not defined in the form classes being used.
    # It is to prevent this data being copied over if for some reason they are
    # added to the forms in the future.
    common_exclude = [
        # Process fields
        "is_active",
        "created",
        "finished",
        "order_datetime",
        # ApplicationBase fields
        "status",
        "submit_datetime",
        "last_submit_datetime",
        "reassign_datetime",
        "reference",
        "decision",
        "refuse_reason",
        # ExportApplicationABC fields
        "last_update_datetime",
        # ExportApplication fields
        "last_updated_by",
        "variation_requests",
        "case_notes",
        "further_information_requests",
        "update_requests",
        "case_emails",
        "submitted_by",
        "created_by",
        "exporter",
        "exporter_office",
        "contact",
        "agent",
        "agent_office",
        "case_owner",
        "cleared_by",
    ]

    copy_app_data(existing_app, new_app, common_exclude, created_by)

    return new_app


def copy_cfs_data(
    existing: CertificateOfFreeSaleApplication,
    new: CertificateOfFreeSaleApplication,
    exclude_fields: list[str],
    created_by: User,
) -> None:
    # Copy main form
    data = model_to_dict(existing, exclude=exclude_fields + ["id"])
    form = EditCFSForm(instance=new, data=data)
    _save_form(form, existing.pk)

    # Copy each schedule
    for existing_schedule in existing.schedules.all():
        # Create an empty schedule before saving template data using form.
        instance = new.schedules.create(created_by=created_by)
        data = model_to_dict(existing_schedule, exclude=["id", "application"])
        form = EditCFScheduleForm(instance=instance, data=data)
        new_schedule: CFSSchedule = _save_form(form, existing.pk)

        # Set the manufacturer data.
        if data.get("manufacturer_name"):
            form = CFSManufacturerDetailsForm(instance=new_schedule, data=data)
            _save_form(form, existing.pk)

        # Copy each product
        for existing_product in existing_schedule.products.all():
            # Create a new product
            data = model_to_dict(existing_product, exclude=["id", "schedule"])
            form = CFSProductForm(schedule=new_schedule, data=data)
            new_product = _save_form(form, existing.pk)

            # Copy any related product_type_numbers to new product
            for product_type in existing_product.product_type_numbers.all():
                data = model_to_dict(product_type, exclude=["id", "product"])
                form = CFSProductTypeForm(product=new_product, data=data)
                _save_form(form, existing.pk)

            # Copy any related active_ingredients to new product
            for active_ingredient in existing_product.active_ingredients.all():
                data = model_to_dict(active_ingredient, exclude=["id", "product"])
                form = CFSActiveIngredientForm(product=new_product, data=data)
                _save_form(form, existing.pk)


def copy_com_data(
    existing: CertificateOfManufactureApplication,
    new: CertificateOfManufactureApplication,
    exclude_fields: list[str],
    created_by: User,
) -> None:
    data = model_to_dict(existing, exclude=exclude_fields + ["id"])
    form = EditCOMForm(instance=new, data=data)
    _save_form(form, existing.pk)


def copy_gmp_data(
    existing: CertificateOfGoodManufacturingPracticeApplication,
    new: CertificateOfGoodManufacturingPracticeApplication,
    exclude_fields: list[str],
    created_by: User,
) -> None:
    data = model_to_dict(existing, exclude=exclude_fields + ["id"])
    form = EditGMPForm(instance=new, data=data)
    _save_form(form, existing.pk)

    add_gmp_country(new)


def add_gmp_country(application: CertificateOfGoodManufacturingPracticeApplication) -> None:
    """GMP applications are for China only"""
    country = application.application_type.country_group.countries.filter(is_active=True).first()
    application.countries.add(country)


def _save_form(form: ModelForm, export_application_pk: int) -> Any:
    if form.is_valid():
        return form.save()
    else:
        error_msg = (
            f"Error copying application using ExportApplication(id={export_application_pk})."
            f" Form errors: {form.errors.as_text()}"
        )

        capture_message(error_msg)

        raise ValidationError(error_msg)
