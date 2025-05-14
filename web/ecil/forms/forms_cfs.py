from typing import Any, Literal

from django.conf import settings
from django.db.models import QuerySet
from django.template.loader import render_to_string
from markupsafe import Markup, escape

from web.domains.case.forms import application_contacts
from web.ecil.gds import forms as gds_forms
from web.models import (
    CertificateOfFreeSaleApplication,
    CFSProduct,
    CFSProductType,
    CFSSchedule,
    Country,
    ProductLegislation,
    User,
)
from web.models.shared import AddressEntryType, YesNoChoices


class CFSApplicationReferenceForm(gds_forms.GDSModelForm):
    applicant_reference = gds_forms.GovUKTextInputField(
        label="Name the application (Optional)",
        help_text=(
            "Give the application a name so you can refer back to it when needed."
            " For example, gloss lipsticks."
            " This is just for your reference and will not appear on the certificate."
        ),
        required=False,
        error_messages={"required": "Enter a name for the application"},
        gds_field_kwargs=gds_forms.LABEL_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CertificateOfFreeSaleApplication
        fields = ["applicant_reference"]


class CFSApplicationContactForm(gds_forms.GDSForm):
    contact = gds_forms.GovUKRadioInputField(
        label="Who is the main contact for your application?",
        help_text="This is usually the person who created the application",
        error_messages={"required": "Select the main contact for your application"},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    def clean_contact(self) -> Literal["none-of-these"] | User:
        contact_pk = self.cleaned_data["contact"]

        if contact_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            return contact_pk

        return self.contacts.get(pk=contact_pk)

    def __init__(
        self, *args: Any, instance: CertificateOfFreeSaleApplication, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.instance = instance

        self.contacts = application_contacts(self.instance)
        contact_list = [(c.pk, c.full_name) for c in self.contacts]
        contact_list.append((gds_forms.GovUKRadioInputField.NONE_OF_THESE, "Someone else"))

        self.fields["contact"].choices = contact_list
        if self.instance.contact:
            self.fields["contact"].initial = self.instance.contact.pk


class CFSScheduleExporterStatusForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["exporter_status"]

    exporter_status = gds_forms.GovUKRadioInputField(
        help_text=Markup(render_to_string("ecil/cfs/help_text/schedule_exporter_status.html")),
        error_messages={"required": "Select yes or no"},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        choices=(
            (CFSSchedule.ExporterStatus.IS_MANUFACTURER, "Yes"),
            (CFSSchedule.ExporterStatus.IS_NOT_MANUFACTURER, "No"),
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["exporter_status"].label = get_schedule_label(
            self.instance, "Is the company the product manufacturer?"
        )


class CFSScheduleManufacturerAddressForm(gds_forms.GDSModelForm):
    manufacturer_address = gds_forms.GovUKTextareaField(label="Company address")

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = [
            "manufacturer_name",
            "manufacturer_address",
            "manufacturer_postcode",
        ]

        labels = {
            "manufacturer_name": " Company name",
            "manufacturer_postcode": "Company postcode",
        }

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={"manufacturer_postcode": {"classes": "govuk-input--width-10"}},
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # For now all fields are optional.
        for f in self.fields:
            self.fields[f].required = False

    def save(self, commit: bool = True) -> CFSSchedule:
        instance = super().save(commit)

        # Set to manual until we implement postcode search
        instance.manufacturer_address_entry_type = AddressEntryType.MANUAL
        if commit:
            instance.save()

        return instance


class CFSScheduleBrandNameHolderForm(gds_forms.GDSModelForm):
    brand_name_holder = gds_forms.GovUKRadioInputField(
        choices=YesNoChoices.choices,
        help_text="The brand name holder has a product marketed under their own name or trademark.",
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        choice_conditional_html={
            YesNoChoices.no: Markup(
                '<p class="govuk-body">Import Licensing Branch will contact you for more information about the brand name holder</p>'
            )
        },
        error_messages={"required": "Select yes or no"},
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["brand_name_holder"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["brand_name_holder"].label = get_schedule_label(
            self.instance, "Is the company the brand name holder for the product?"
        )


class CFSScheduleCountryOfManufactureForm(gds_forms.GDSModelForm):
    country_of_manufacture = gds_forms.GovUKSelectModelField(
        help_text=(
            "Enter a country or territory and select it from the results."
            " You can only add one."
            " Create another product schedule for any product manufactured in a different country"
            " or territory."
        ),
        queryset=Country.objects.none(),
        error_messages={"required": "Add a country or territory"},
        gds_field_kwargs=gds_forms.LABEL_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["country_of_manufacture"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["country_of_manufacture"].queryset = Country.app.get_cfs_com_countries()
        self.fields["country_of_manufacture"].label = get_schedule_label(
            self.instance, "Where is the product manufactured?"
        )


class CFSScheduleAddLegislationForm(gds_forms.GDSModelForm):
    legislations = gds_forms.GovUKSelectModelField(
        help_text=Markup(
            render_to_string(
                template_name="ecil/cfs/help_text/schedule_legislations.html",
                context={"ilb_contact_email": settings.ILB_CONTACT_EMAIL},
            ),
        ),
        queryset=ProductLegislation.objects.none(),
        error_messages={"required": "Add a legislation that applies to the product"},
        gds_field_kwargs=gds_forms.LABEL_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["legislations"]

    def __init__(self, *args: Any, initial: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not initial:
            initial = {}

        # legislations is a ManyToMany and sets the initial value to a list.
        # A list is not a supported value for gds_forms.GovUKSelectModelField.
        # This form is for adding legislations only so override the initial value to "".
        initial["legislations"] = ""
        super().__init__(*args, initial=initial, **kwargs)
        self.selected_legislations = self.instance.legislations.all().values_list("id", flat=True)

        if len(self.selected_legislations) == 0:
            label = "Which legislation applies to the product?"
        else:
            label = "Add another legislation"
        self.fields["legislations"].label = get_schedule_label(self.instance, label)
        self.fields["legislations"].queryset = self.get_legislations_queryset()

    def clean(self) -> None:
        cleaned_data = super().clean()

        if (
            self.selected_legislations
            and cleaned_data.get("legislations")
            and len(self.selected_legislations) >= 3
        ):
            self.add_error("legislations", "You can only add up to 3 legislations")

        return cleaned_data

    def get_legislations_queryset(self) -> QuerySet[ProductLegislation]:
        active_legislations = ProductLegislation.objects.filter(is_active=True)

        if self.instance.application.exporter_office.is_in_northern_ireland:
            legislation_qs = active_legislations.filter(ni_legislation=True)
        else:
            legislation_qs = active_legislations.filter(gb_legislation=True)

        return legislation_qs.order_by("name")

    def _save_m2m(self):
        """Custom method to save the new legislation to the set of existing legislations."""
        new_legislation = self.cleaned_data["legislations"]
        self.instance.legislations.add(new_legislation)


class CFSScheduleAddAnotherLegislationForm(gds_forms.GDSForm):
    add_another = gds_forms.GovUKRadioInputField(
        label="Do you need to add another legislation?",
        choices=YesNoChoices.choices,
        gds_field_kwargs={"fieldset": {"legend": {"classes": "govuk-fieldset__legend--m"}}},
        error_messages={"required": "Select yes or no"},
    )


class CFSScheduleRemoveLegislationForm(gds_forms.GDSForm):
    are_you_sure = gds_forms.GovUKRadioInputField(
        choices=YesNoChoices.choices,
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        error_messages={"required": "Select yes or no"},
    )

    def __init__(
        self, *args: Any, schedule: CFSSchedule, legislation: ProductLegislation, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.legislation = legislation
        self.fields["are_you_sure"].label = get_schedule_label(
            schedule, "Are you sure you want to remove this legislation?"
        )
        self.fields["are_you_sure"].help_text = Markup(
            render_to_string(
                template_name="ecil/cfs/help_text/schedule_remove_legislation.html",
                context={"legislation_text": legislation.name},
            ),
        )


class CFSScheduleProductStandardForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["product_standard"]
        error_messages = {"product_standard": {"required": "Select a statement"}}
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={"product_standard": gds_forms.FIELDSET_LEGEND_HEADER},
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        model_label = self.fields["product_standard"].label
        self.fields["product_standard"].label = get_schedule_label(self.instance, model_label)

    def save(self, commit: bool = True) -> CFSSchedule:
        self.instance = super().save(commit)

        self._save_product_standard_fields()

        if commit:
            self.instance.save()

        return self.instance

    def _save_product_standard_fields(self) -> None:
        # "It meets safety standards and is currently being sold on the UK market"
        if self.instance.product_standard == CFSSchedule.ProductStandards.PRODUCT_SOLD_ON_UK_MARKET:
            self.instance.product_eligibility = CFSSchedule.ProductEligibility.SOLD_ON_UK_MARKET
            self.instance.goods_placed_on_uk_market = YesNoChoices.yes
            self.instance.goods_export_only = YesNoChoices.no

        # "It meets safety standards and will be sold on the UK market in the future"
        elif (
            self.instance.product_standard == CFSSchedule.ProductStandards.PRODUCT_FUTURE_UK_MARKET
        ):
            self.instance.product_eligibility = (
                CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY
            )
            self.instance.goods_placed_on_uk_market = YesNoChoices.yes
            self.instance.goods_export_only = YesNoChoices.no

        # "It meets safety standards and is for export only"
        elif self.instance.product_standard == CFSSchedule.ProductStandards.PRODUCT_EXPORT_ONLY:
            self.instance.product_eligibility = (
                CFSSchedule.ProductEligibility.MEET_UK_PRODUCT_SAFETY
            )
            self.instance.goods_placed_on_uk_market = YesNoChoices.no
            self.instance.goods_export_only = YesNoChoices.yes


class CFSScheduleStatementIsResponsiblePersonForm(gds_forms.GDSModelForm):
    schedule_statements_is_responsible_person = gds_forms.GovUKRadioInputField(
        choices=[
            (
                "True",
                "Yes, I am is the responsible person for the product",
            ),
            (
                "False",
                "No, I am a third party exporter and not the responsible person for the product",
            ),
        ],
        error_messages={"required": "Select yes or no"},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
    )

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["schedule_statements_is_responsible_person"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["schedule_statements_is_responsible_person"].label = get_schedule_label(
            self.instance, "Are you the responsible person for the product?"
        )

        is_ni_eu_cosmetics_regulation = self.instance.legislations.filter(
            is_active=True, is_eu_cosmetics_regulation=True, ni_legislation=True
        ).exists()

        self.fields["schedule_statements_is_responsible_person"].help_text = Markup(
            render_to_string(
                template_name="ecil/cfs/help_text/schedule_statements_is_responsible_person.html",
                context={"is_ni_eu_cosmetics_regulation": is_ni_eu_cosmetics_regulation},
            ),
        )


class CFSScheduleStatementAccordanceWithStandardsForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSSchedule
        fields = ["schedule_statements_accordance_with_standards"]
        error_messages = {
            "schedule_statements_accordance_with_standards": {"required": "Select yes or no"}
        }
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "schedule_statements_accordance_with_standards": gds_forms.FIELDSET_LEGEND_HEADER
            },
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields["schedule_statements_accordance_with_standards"].label = get_schedule_label(
            self.instance,
            "Are these products manufactured in accordance with the Good Manufacturing Practice standards set out in UK law?",
        )
        self.fields["schedule_statements_accordance_with_standards"].help_text = Markup(
            render_to_string(
                template_name="ecil/cfs/help_text/schedule_statements_accordance_with_standards.html",
            ),
        )


class CFSScheduleAddProductMethodForm(gds_forms.GDSForm):
    MANUAL = "manual"
    IN_BULK = "in_bulk"

    method = gds_forms.GovUKRadioInputField(
        choices=(
            (MANUAL, "Add one at a time"),
            (IN_BULK, "Add in bulk"),
        ),
        choice_hints={IN_BULK: "Upload multiple products using a spreadsheet"},
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        error_messages={"required": "Select how you want to add your products"},
    )

    def __init__(self, *args: Any, schedule: CFSSchedule, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["method"].label = get_schedule_label(
            schedule, "How do you want to add products?"
        )


class CFSScheduleProductForm(gds_forms.GDSModelForm):
    product_name = gds_forms.GovUKTextInputField(
        label="What is the product name?",
        help_text="Make sure the product name is spelled correctly",
        error_messages={"required": "Add a product name"},
    )
    is_raw_material = gds_forms.GovUKCheckboxesBooleanField(
        label="", help_text="The item is a raw material"
    )

    instance: CFSProduct

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSProduct
        fields = ["product_name", "is_raw_material"]

    def __init__(self, *args: Any, schedule: CFSSchedule, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.schedule = schedule

    def clean_product_name(self) -> str:
        product_name = self.cleaned_data["product_name"]

        if (
            self.schedule.products.filter(product_name__iexact=product_name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            self.add_error("product_name", "Product name must be unique to the schedule.")

        return product_name

    def save(self, commit: bool = True) -> CFSProduct:
        self.instance.schedule = self.schedule
        self.instance = super().save(commit)

        if commit:
            self.instance.save()

        return self.instance


class CFSScheduleProductEndUseForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSProduct
        fields = ["product_end_use"]
        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={"product_end_use": gds_forms.LABEL_HEADER},
        )
        error_messages = {"product_end_use": {"required": "Enter a finished product use"}}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        product: CFSProduct = self.instance

        if product.is_raw_material:
            # raw material label / helptext
            label = f"What is the finished product use for {escape(product.product_name)}?"
            help_text: Markup | str = Markup(
                render_to_string(
                    template_name="ecil/cfs/help_text/schedule_raw_material_product_end_use.html",
                ),
            )
            required = True
        else:
            # Non raw material label / helptext
            label = f"What is {escape(product.product_name)} used for? (Optional)"
            help_text = "For example, shampoo"
            required = False

        self.fields["product_end_use"].label = get_schedule_label(product.schedule, label)
        self.fields["product_end_use"].help_text = help_text
        self.fields["product_end_use"].required = required


class CFSScheduleProductAddAnotherForm(gds_forms.GDSForm):
    add_another = gds_forms.GovUKRadioInputField(
        label="Do you need to add another product?",
        choices=YesNoChoices.choices,
        gds_field_kwargs={"fieldset": {"legend": {"classes": "govuk-fieldset__legend--m"}}},
        error_messages={"required": "Select yes or no"},
    )


class CFSScheduleProductConfirmRemoveForm(gds_forms.GDSForm):
    are_you_sure = gds_forms.GovUKRadioInputField(
        choices=YesNoChoices.choices,
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        error_messages={"required": "Select yes or no"},
    )

    def __init__(self, *args: Any, product: CFSProduct, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["are_you_sure"].label = get_schedule_label(
            product.schedule, f"Are you sure you want to remove {escape(product.product_name)}?"
        )


class CFSScheduleProductTypeForm(gds_forms.GDSModelForm):
    product_type_number = gds_forms.GovUKIntegerField(
        help_text=(
            "A product type number indicates what product type group biocide chemicals are in."
            " They always start with PT."
            " For example, the product type number for human hygiene products is PT 1."
        ),
        gds_field_kwargs=gds_forms.LABEL_HEADER
        | {"prefix": {"text": "PT"}, "classes": "govuk-input--width-10"},
        error_messages={
            "required": "Enter a product type number",
            "invalid_choice": "Enter a product type number between 1 and 22",
        },
    )

    instance: CFSProductType

    class Meta(gds_forms.GDSModelForm.Meta):
        model = CFSProductType
        fields = ["product_type_number"]

    def __init__(self, *args: Any, product: CFSProduct, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.product = product

        if self.product.product_type_numbers.exists():
            label = f"Add another product type number for {escape(product.product_name)}"
        else:
            label = f"What is the product type number for {escape(product.product_name)}?"

        self.fields["product_type_number"].label = get_schedule_label(product.schedule, label)

    def clean_product_type_number(self) -> str:
        product_type_number = self.cleaned_data["product_type_number"]

        if (
            self.product.product_type_numbers.filter(product_type_number=product_type_number)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            self.add_error(
                "product_type_number",
                f"PT{product_type_number} has already been added to this product.",
            )

        return product_type_number

    def save(self, commit: bool = True) -> CFSProductType:
        self.instance.product = self.product
        self.instance = super().save(commit)

        if commit:
            self.instance.save()

        return self.instance


class CFSScheduleProductTypeAddAnotherForm(gds_forms.GDSForm):
    add_another = gds_forms.GovUKRadioInputField(
        label="Do you need to add another product type number?",
        choices=YesNoChoices.choices,
        gds_field_kwargs={"fieldset": {"legend": {"classes": "govuk-fieldset__legend--m"}}},
        error_messages={"required": "Select yes or no"},
    )


class CFSScheduleProductTypeConfirmRemoveForm(gds_forms.GDSForm):
    are_you_sure = gds_forms.GovUKRadioInputField(
        choices=YesNoChoices.choices,
        gds_field_kwargs=gds_forms.FIELDSET_LEGEND_HEADER,
        error_messages={"required": "Select yes or no"},
    )

    def __init__(self, *args: Any, product_type: CFSProductType, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["are_you_sure"].label = get_schedule_label(
            product_type.product.schedule,
            f"Are you sure you want to remove product type number PT {escape(product_type.product_type_number)}?",
        )


def get_schedule_label(schedule: CFSSchedule, label: str) -> Markup:
    """Return a schedule label.

    This function returns Markup, therefore any user defined content in label must be escaped first.
    """
    schedule_num = get_schedule_number(schedule)

    return Markup(f'<span class="govuk-caption-l">Product schedule {schedule_num}</span>{label}')


def get_schedule_number(schedule: CFSSchedule) -> int:
    for idx, s in enumerate(schedule.application.schedules.order_by("created_at"), start=1):
        if s.pk == schedule.pk:
            return idx

    return 1
