from django.core.exceptions import ValidationError
from django.db import models
from django.forms import ModelForm, model_to_dict

from web.domains.case.export.forms import (
    CFSActiveIngredientForm,
    CFSManufacturerDetailsForm,
    CFSProductForm,
    CFSProductTypeForm,
    EditCFSForm,
    EditCFSScheduleForm,
    EditCOMForm,
    EditGMPForm,
)
from web.domains.cat.forms import (
    CertificateOfFreeSaleApplicationTemplateForm,
    CertificateOfGoodManufacturingPracticeApplicationTemplateForm,
    CertificateOfManufactureApplicationTemplateForm,
    CFSActiveIngredientTemplateForm,
    CFSManufacturerDetailsTemplateForm,
    CFSProductTemplateForm,
    CFSProductTypeTemplateForm,
    CFSScheduleTemplateForm,
)
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfFreeSaleApplicationTemplate,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfGoodManufacturingPracticeApplicationTemplate,
    CertificateOfManufactureApplication,
    CertificateOfManufactureApplicationTemplate,
    CFSSchedule,
    CFSScheduleTemplate,
    Country,
    User,
)
from web.utils.sentry import capture_message


class ApplicationCopy:
    """Class to copy data between export applications and certificate application templates."""

    edit_form: type[ModelForm]
    edit_template_form: type[ModelForm]

    def __init__(self, existing: models.Model, new: models.Model, created_by: User) -> None:
        """

        :param existing: An application or template instance.
        :param new: An application or template instance.
        :param created_by: User who created the new application or template.
        """

        self.existing = existing
        self.new = new
        self.created_by = created_by

    def copy_application_to_application(self) -> None:
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

        self._copy_edit_form(self.edit_form, exclude_fields=common_exclude)

    def copy_application_to_template(self) -> None:
        self._copy_edit_form(self.edit_template_form)

    def copy_template_to_application(self) -> None:
        common_exclude = ["template"]

        self._copy_edit_form(self.edit_form, exclude_fields=common_exclude)

    def _copy_edit_form(
        self, edit_form: type[ModelForm], exclude_fields: list | None = None
    ) -> None:
        if not exclude_fields:
            exclude_fields = []

        data = model_to_dict(self.existing, exclude=exclude_fields + ["id"])
        form = edit_form(instance=self.new, data=data)
        self.save_form(form)

    def save_form(self, form: ModelForm) -> models.Model:
        if form.is_valid():
            return form.save()
        else:
            error_msg = (
                f"Error copying data using {self.existing!r})."
                f" Form errors: {form.errors.as_text()}"
            )

            capture_message(error_msg)

            raise ValidationError(error_msg)


class COMApplicationCopy(ApplicationCopy):
    edit_form = EditCOMForm
    edit_template_form = CertificateOfManufactureApplicationTemplateForm

    # Extra type hints
    existing: CertificateOfManufactureApplication | CertificateOfManufactureApplicationTemplate
    new: CertificateOfManufactureApplication | CertificateOfManufactureApplicationTemplate


class GMPApplicationCopy(ApplicationCopy):
    edit_form = EditGMPForm
    edit_template_form = CertificateOfGoodManufacturingPracticeApplicationTemplateForm

    # Extra type hints
    existing: (
        CertificateOfGoodManufacturingPracticeApplication
        | CertificateOfGoodManufacturingPracticeApplicationTemplate
    )
    new: (
        CertificateOfGoodManufacturingPracticeApplication
        | CertificateOfGoodManufacturingPracticeApplicationTemplate
    )

    def copy_application_to_application(self) -> None:
        super().copy_application_to_application()

        # GMP applications are for China only
        country = Country.app.get_gmp_countries().first()
        self.new.countries.add(country)


class CFSApplicationCopy(ApplicationCopy):
    edit_form = EditCFSForm
    edit_template_form = CertificateOfFreeSaleApplicationTemplateForm

    # Extra type hints
    existing: CertificateOfFreeSaleApplication | CertificateOfFreeSaleApplicationTemplate
    new: CertificateOfFreeSaleApplication | CertificateOfFreeSaleApplicationTemplate

    def copy_application_to_application(self) -> None:
        super().copy_application_to_application()

        for existing_schedule in self.existing.schedules.all():
            self.copy_schedule(
                existing_schedule,
                EditCFSScheduleForm,
                CFSManufacturerDetailsForm,
                CFSProductForm,
                CFSProductTypeForm,
                CFSActiveIngredientForm,
            )

    def copy_application_to_template(self) -> None:
        super().copy_application_to_template()

        for existing_schedule in self.existing.schedules.all():
            self.copy_schedule(
                existing_schedule,
                CFSScheduleTemplateForm,
                CFSManufacturerDetailsTemplateForm,
                CFSProductTemplateForm,
                CFSProductTypeTemplateForm,
                CFSActiveIngredientTemplateForm,
            )

    def copy_template_to_application(self) -> None:
        super().copy_template_to_application()

        for existing_schedule in self.existing.schedules.all():
            self.copy_schedule(
                existing_schedule,
                EditCFSScheduleForm,
                CFSManufacturerDetailsForm,
                CFSProductForm,
                CFSProductTypeForm,
                CFSActiveIngredientForm,
            )

    def copy_schedule(
        self,
        existing_schedule: CFSSchedule | CFSScheduleTemplate,
        edit_schedule_form: type[EditCFSScheduleForm | CFSScheduleTemplateForm],
        manufacturer_details_form: type[
            CFSManufacturerDetailsForm | CFSManufacturerDetailsTemplateForm
        ],
        product_form: type[CFSProductForm | CFSProductTemplateForm],
        product_type_form: type[CFSProductTypeForm | CFSProductTypeTemplateForm],
        active_ingredient_form: type[CFSActiveIngredientForm | CFSActiveIngredientTemplateForm],
    ) -> None:
        instance = self.new.schedules.create(created_by=self.created_by)
        data = model_to_dict(existing_schedule, exclude=["id", "application", "created_by"])
        form = edit_schedule_form(instance=instance, data=data)
        new_schedule: CFSSchedule | CFSScheduleTemplate = self.save_form(form)

        # Set the manufacturer data.
        if data.get("manufacturer_name"):
            form = manufacturer_details_form(instance=new_schedule, data=data)
            self.save_form(form)

        # Copy each product
        for existing_product in existing_schedule.products.all():
            # Create a new product
            data = model_to_dict(existing_product, exclude=["id", "schedule"])
            form = product_form(schedule=new_schedule, data=data)
            new_product = self.save_form(form)

            # Copy any related product_type_numbers to new product
            for product_type in existing_product.product_type_numbers.all():
                data = model_to_dict(product_type, exclude=["id", "product"])
                form = product_type_form(product=new_product, data=data)
                self.save_form(form)

            # Copy any related active_ingredients to new product
            for active_ingredient in existing_product.active_ingredients.all():
                data = model_to_dict(active_ingredient, exclude=["id", "product"])
                form = active_ingredient_form(product=new_product, data=data)
                self.save_form(form)
