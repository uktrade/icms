import re
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_select2.forms import ModelSelect2Widget, Select2MultipleWidget
from guardian.shortcuts import get_objects_for_user

import web.forms.widgets as icms_widgets
from web.domains.case.forms import application_contacts
from web.domains.file.utils import ICMSFileField
from web.forms.mixins import OptionalFormMixin
from web.models import (
    CertificateApplicationTemplate,
    Exporter,
    Office,
    ProductLegislation,
    User,
)
from web.models.shared import AddressEntryType, YesNoChoices
from web.permissions import Perms
from web.utils import is_northern_ireland_postcode

from .models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
    ExportApplicationType,
)


class CreateExportApplicationForm(forms.Form):
    exporter = forms.ModelChoiceField(
        queryset=Exporter.objects.none(),
        label="Main Exporter",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Exporter",
            },
            search_fields=("name__icontains"),
        ),
    )
    exporter_office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        label="Exporter Office",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Office",
            },
            search_fields=(
                "postcode__icontains",
                "address_1__icontains",
                "address_2__icontains",
                "address_3__icontains",
                "address_4__icontains",
                "address_5__icontains",
                "address_6__icontains",
                "address_7__icontains",
                "address_8__icontains",
            ),
            dependent_fields={"exporter": "exporter"},
        ),
        help_text="The office that this certificate will be issued to.",
    )

    agent = forms.ModelChoiceField(
        required=False,
        queryset=Exporter.objects.none(),
        label="Agent of Exporter",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Agent",
            },
            search_fields=("name__icontains",),
            # Key is a name of a field in a form.
            # Value is a name of a field in a model (used in `queryset`).
            dependent_fields={"exporter": "main_exporter"},
        ),
    )
    agent_office = forms.ModelChoiceField(
        required=False,
        queryset=Office.objects.none(),
        label="Agent Office",
        widget=ModelSelect2Widget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Select Office",
            },
            search_fields=(
                "postcode__icontains",
                "address_1__icontains",
                "address_2__icontains",
                "address_3__icontains",
                "address_4__icontains",
                "address_5__icontains",
                "address_6__icontains",
                "address_7__icontains",
                "address_8__icontains",
            ),
            # Key is a name of a field in a form.
            # Value is a name of a field in a model (used in `queryset`).
            dependent_fields={"agent": "exporter"},
        ),
    )

    def __init__(
        self,
        *args: Any,
        user: User,
        cat: CertificateApplicationTemplate | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.user = user
        self.cat = cat

        # Return main exporters the user can edit or is an agent of.
        exporters = get_objects_for_user(
            user,
            [Perms.obj.exporter.edit, Perms.obj.exporter.is_agent],
            Exporter.objects.filter(is_active=True, main_exporter__isnull=True),
            any_perm=True,
        )
        self.fields["exporter"].queryset = exporters
        self.fields["exporter_office"].queryset = Office.objects.filter(
            is_active=True, exporter__in=exporters
        )

        # Return agents linked to exporters the user can edit (if any)
        active_agents = Exporter.objects.filter(is_active=True, main_exporter__in=exporters)
        agents = get_objects_for_user(user, [Perms.obj.exporter.edit], active_agents)

        self.fields["agent"].queryset = agents
        self.fields["agent_office"].queryset = Office.objects.filter(
            is_active=True, exporter__in=agents
        )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        exporter = cleaned_data.get("exporter")
        # if exporter is not set agent and agent_office are not displayed.
        if not exporter:
            return cleaned_data

        is_agent = self.user.has_perm(Perms.obj.exporter.is_agent, exporter)

        if is_agent:
            if not cleaned_data.get("agent"):
                self.add_error("agent", "You must enter this item")

            if not cleaned_data.get("agent_office"):
                self.add_error("agent_office", "You must enter this item")

        return cleaned_data

    def clean_exporter_office(self) -> Office:
        office = self.cleaned_data["exporter_office"]

        # CFS CAT specific check
        if self.cat and self.cat.application_type == ExportApplicationType.Types.FREE_SALE:
            # Check that the template and exporter office match
            is_ni_app = office.is_in_northern_ireland
            is_ni_template = self.cat.is_ni_template

            if is_ni_template != is_ni_app:
                if is_ni_template:
                    msg = "Cannot copy a Northern Ireland Template to a GB CFS Application"
                else:
                    msg = "Cannot copy a GB Template to a Northern Ireland CFS Application"

                raise ValidationError(msg)

        return office


class PrepareCertManufactureFormBase(forms.ModelForm):
    is_pesticide_on_free_sale_uk_error_msg = mark_safe(
        '<div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>'
        "<p>A Certificate of Manufacture cannot be completed for a pesticide on free sale in the UK.</p>"
        "<p>To process this request contact the following:</p>"
        "<ul>"
        '<li>Agricultural pesticides - <a href="mailto:asg@hse.gov.uk">asg@hse.gov.uk</a>'  # /PS-IGNORE
        '<li>Non-agricultural pesticides - <a href="mailto:biocidesenquiries@hse.gov.uk">biocidesenquiries@hse.gov.uk</a>'  # /PS-IGNORE
        "</ul>"
        "</div>"
    )

    is_manufacturer_error_msg = mark_safe(
        '<div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>'
        "<p>A Certificate of Manufacture can only be applied for by the manufacturer of the pesticide.</p>"
        "</div>"
    )

    class Meta:
        model = CertificateOfManufactureApplication

        fields = [
            "contact",
            "countries",
            "is_pesticide_on_free_sale_uk",
            "is_manufacturer",
            "product_name",
            "chemical_name",
            "manufacturing_process",
        ]

        help_texts = {
            "manufacturing_process": "Please provide an outline of the process.",
        }

        labels = {
            "is_pesticide_on_free_sale_uk": "Is the pesticide on free sale in the UK?",
            "is_manufacturer": "Is the applicant company the manufacturer of the pesticide?",
        }

        widgets = {
            "countries": Select2MultipleWidget,
            "is_pesticide_on_free_sale_uk": icms_widgets.YesNoRadioSelectInline,
            "is_manufacturer": icms_widgets.YesNoRadioSelectInline,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_pesticide_on_free_sale_uk"].required = True
        self.fields["is_manufacturer"].required = True
        self.fields["product_name"].required = True
        self.fields["chemical_name"].required = True
        self.fields["manufacturing_process"].required = True

        self.fields["countries"].queryset = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ).country_group.countries.filter(is_active=True)

        # Contact isn't a field in the template.
        if "contact" in self.fields:
            self.fields["contact"].queryset = application_contacts(self.instance)

    def clean_is_pesticide_on_free_sale_uk(self):
        """Perform extra logic even thought this is the edit form where every field is optional"""

        val: bool | None = self.cleaned_data["is_pesticide_on_free_sale_uk"]

        if val:
            raise forms.ValidationError(self.is_pesticide_on_free_sale_uk_error_msg)

        return val

    def clean_is_manufacturer(self):
        """Perform extra logic even thought this is the edit form where every field is optional"""

        val: bool | None = self.cleaned_data["is_manufacturer"]

        if val is False:
            raise forms.ValidationError(self.is_manufacturer_error_msg)

        return val


class EditCOMForm(OptionalFormMixin, PrepareCertManufactureFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitCOMForm(PrepareCertManufactureFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean_is_pesticide_on_free_sale_uk(self):
        val = self.cleaned_data["is_pesticide_on_free_sale_uk"]

        if val is None:
            raise forms.ValidationError("You must enter this item.")

        if val:
            raise forms.ValidationError(self.is_pesticide_on_free_sale_uk_error_msg)

        return val

    def clean_is_manufacturer(self):
        val = self.cleaned_data["is_manufacturer"]

        if val is None:
            raise forms.ValidationError("You must enter this item.")

        if not val:
            raise forms.ValidationError(self.is_manufacturer_error_msg)

        return val


class EditCFSFormBase(forms.ModelForm):
    class Meta:
        model = CertificateOfFreeSaleApplication

        fields = (
            "contact",
            "countries",
        )

        widgets = {
            "countries": Select2MultipleWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "Select Country",
                    "data-maximum-selection-length": 40,
                },
            )
        }


class EditCFSForm(OptionalFormMixin, EditCFSFormBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Contact isn't a field in the template.
        if "contact" in self.fields:
            self.fields["contact"].queryset = application_contacts(self.instance)

        self.fields["countries"].queryset = ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.FREE_SALE
        ).country_group.countries.filter(is_active=True)


class SubmitCFSForm(EditCFSFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class CFSScheduleFormBase(forms.ModelForm):
    class Meta:
        model = CFSSchedule
        fields = (
            "exporter_status",
            "brand_name_holder",
            "legislations",
            "biocidal_claim",
            "product_eligibility",
            "goods_placed_on_uk_market",
            "goods_export_only",
            "any_raw_materials",
            "final_product_end_use",
            "country_of_manufacture",
            "schedule_statements_accordance_with_standards",
            "schedule_statements_is_responsible_person",
        )

        widgets = {
            "exporter_status": icms_widgets.RadioSelect,
            "brand_name_holder": icms_widgets.RadioSelectInline,
            "product_eligibility": icms_widgets.RadioSelect,
            "goods_placed_on_uk_market": icms_widgets.RadioSelectInline,
            "goods_export_only": icms_widgets.RadioSelectInline,
            "any_raw_materials": icms_widgets.RadioSelectInline,
            "legislations": Select2MultipleWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "Select Legislation",
                    "data-maximum-selection-length": 3,
                },
            ),
            "biocidal_claim": icms_widgets.RadioSelectInline,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        legislation_qs = self.get_legislations_queryset()
        self.fields["legislations"].queryset = legislation_qs.order_by("name")

        # the help-text for this field contains HTML markup, and it's nicer to render an HTML file than add raw HTML
        # in Python
        self.fields["biocidal_claim"].help_text = render_to_string(
            "web/domains/case/export/partials/cfs/biocidal_claim_help_text.html"
        )
        # The biocidal_claim field has an empty choice of "----" as it's not a fundamentally
        # required field (it's conditional) so we can't have blank=False on the model
        # to stop it from ever appearing, so we remove it manually now.
        self.fields["biocidal_claim"].empty_label = None

        # the value of this field is determined by the value of the goods_placed_on_uk_market field
        self.fields["goods_export_only"].disabled = True

    def clean(self):
        cleaned_data = self.cleaned_data
        biocidal_claim = cleaned_data.get("biocidal_claim", False)
        legislations = cleaned_data.get("legislations", ProductLegislation.objects.none())
        if not biocidal_claim and legislations.filter(is_biocidal_claim=True).exists():
            self.add_error("biocidal_claim", "This field is required.")

        return cleaned_data

    def save(self, commit=True):
        # we want to manually set the goods_export_only field based on the goods_placed_on_uk_market field.
        # because the goods_export_field is disabled, it is not included in the form data, so we need to set it manually
        if self.instance.goods_placed_on_uk_market == YesNoChoices.no:
            self.instance.goods_export_only = YesNoChoices.yes
        elif self.instance.goods_placed_on_uk_market == YesNoChoices.yes:
            self.instance.goods_export_only = YesNoChoices.no
        return super().save(commit=commit)

    def get_legislations_queryset(self) -> QuerySet[ProductLegislation]:
        legislation_qs = ProductLegislation.objects.filter(is_active=True)

        if self.instance.application.exporter_office.is_in_northern_ireland:
            legislation_qs = legislation_qs.filter(ni_legislation=True)
        else:
            legislation_qs = legislation_qs.filter(gb_legislation=True)

        return legislation_qs


class EditCFScheduleForm(OptionalFormMixin, CFSScheduleFormBase):
    """Form used when editing the CFS schedule.

    All fields are optional to allow partial record saving.
    """


class SubmitCFSScheduleForm(CFSScheduleFormBase):
    """Form used when submitting the CFS schedule.

    All fields are fully validated to ensure form is correct.
    """

    def clean(self):
        cleaned_data: dict[str, Any] = super().clean()

        if not self.is_valid():
            return cleaned_data

        # Check any raw materials field
        any_raw_materials: str = cleaned_data["any_raw_materials"]
        final_product_end_use: str | None = cleaned_data["final_product_end_use"]

        if any_raw_materials == YesNoChoices.yes and not final_product_end_use:
            self.add_error("final_product_end_use", "You must enter this item")

        # Clear the final_product_end_use data if not needed.
        elif any_raw_materials == YesNoChoices.no:
            cleaned_data["final_product_end_use"] = ""

        # Check goods field
        goods_placed_on_uk_market: str = cleaned_data["goods_placed_on_uk_market"]
        goods_export_only: str = cleaned_data["goods_export_only"]

        if goods_placed_on_uk_market == YesNoChoices.yes and goods_export_only == YesNoChoices.yes:
            self.add_error("goods_placed_on_uk_market", "Both of these fields cannot be yes")
            self.add_error("goods_export_only", "Both of these fields cannot be yes")

        # check legislations do not exceed three
        legislations: QuerySet[ProductLegislation] = self.cleaned_data["legislations"]

        if legislations.count() > 3:
            self.add_error("legislations", "You must enter no more than 3 items.")

        # Check if legislation is not biocidal but products contain ingredients and product type numbers
        is_biocidal = legislations.filter(is_biocidal=True).exists()

        if is_biocidal:
            return cleaned_data

        if self.instance.products.exclude(active_ingredients=None).count() > 0:
            self.add_error(
                "legislations",
                "Only biocidal legislation can contain products with active ingredients. Please edit the products.",
            )

        if self.instance.products.exclude(product_type_numbers=None).count() > 0:
            self.add_error(
                "legislations",
                "Only biocidal legislation can contain products with product type numbers. Please edit the products.",
            )

        return cleaned_data


class CFSManufacturerDetailsForm(forms.ModelForm):
    class Meta:
        model = CFSSchedule

        fields = (
            "manufacturer_name",
            "manufacturer_address_entry_type",
            "manufacturer_postcode",
            "manufacturer_address",
        )

        widgets = {
            "manufacturer_address": forms.Textarea,
            "manufacturer_address_entry_type": icms_widgets.RadioSelectInline,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            if self.instance.manufacturer_address_entry_type == AddressEntryType.SEARCH:
                self.fields["manufacturer_address"].widget.attrs["readonly"] = True

    def clean(self):
        cleaned_data = super().clean()

        postcode = cleaned_data.get("manufacturer_postcode")
        address = cleaned_data.get("manufacturer_address")

        if postcode and not address:
            self.add_error("manufacturer_address", "You must enter this item")


class CFSProductForm(forms.ModelForm):
    class Meta:
        model = CFSProduct
        fields = ("product_name",)

    def __init__(self, *args: Any, schedule: CFSSchedule, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.schedule = schedule

    def clean_product_name(self):
        product_name = self.cleaned_data["product_name"]

        if (
            self.schedule.products.filter(product_name__iexact=product_name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Product name must be unique to the schedule.")

        return product_name

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.schedule = self.schedule

        return super().save(commit=commit)


class CFSProductFormSetBase(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index: int) -> dict[str, Any]:
        kwargs = super().get_form_kwargs(index)

        return kwargs | {"schedule": self.instance}


CFSProductFormSet = forms.inlineformset_factory(
    CFSSchedule,
    CFSProduct,
    form=CFSProductForm,
    formset=CFSProductFormSetBase,
    extra=5,
)


class CFSProductTypeForm(forms.ModelForm):
    class Meta:
        model = CFSProductType
        fields = ("product_type_number",)

    def __init__(self, *args: Any, product: CFSProduct, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_product_type_number(self):
        product_type_number = self.cleaned_data["product_type_number"]

        if (
            self.product.product_type_numbers.filter(product_type_number=product_type_number)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Product type number must be unique to the product.")

        return product_type_number

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.product = self.product

        return super().save(commit=commit)


class CFSActiveIngredientForm(forms.ModelForm):
    class Meta:
        model = CFSProductActiveIngredient
        fields = ("name", "cas_number")

    def __init__(self, *args: Any, product: CFSProduct, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_cas_number(self):
        cas_number = self.cleaned_data["cas_number"]

        # TODO: What is the validation for cas number?
        if not re.match("[1-9]{1}[0-9]{1,5}-[0-9]{2}-[0-9]", cas_number):
            raise forms.ValidationError("CAS number is in an incorrect format.")

        if (
            self.product.active_ingredients.filter(cas_number=cas_number)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("CAS number must be unique to the product.")

        return cas_number

    def clean_name(self):
        name = self.cleaned_data["name"]

        if (
            self.product.active_ingredients.filter(name__iexact=name)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Active ingredient name must be unique to the product.")

        return name

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.product = self.product

        return super().save(commit=commit)


class ProductsFileUploadForm(forms.Form):
    file = ICMSFileField()


class EditGMPFormBase(forms.ModelForm):
    """Base class for all GMP forms (editing and creating from a template)"""

    class Meta:
        model = CertificateOfGoodManufacturingPracticeApplication

        fields = (
            "brand_name",
            "contact",
            "is_manufacturer",
            "is_responsible_person",
            "manufacturer_address",
            "manufacturer_address_entry_type",
            "manufacturer_country",
            "manufacturer_name",
            "manufacturer_postcode",
            "responsible_person_address",
            "responsible_person_address_entry_type",
            "responsible_person_country",
            "responsible_person_name",
            "responsible_person_postcode",
            "gmp_certificate_issued",
            "auditor_accredited",
            "auditor_certified",
        )

        widgets = {
            "is_manufacturer": icms_widgets.RadioSelectInline,
            "is_responsible_person": icms_widgets.RadioSelectInline,
            "manufacturer_address": forms.Textarea,
            "manufacturer_country": icms_widgets.RadioSelect,
            "manufacturer_address_entry_type": icms_widgets.RadioSelectInline,
            "responsible_person_address_entry_type": icms_widgets.RadioSelectInline,
            "responsible_person_address": forms.Textarea,
            "responsible_person_country": icms_widgets.RadioSelect,
            "gmp_certificate_issued": icms_widgets.RadioSelect,
            "auditor_accredited": icms_widgets.RadioSelectInline,
            "auditor_certified": icms_widgets.RadioSelectInline,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            if self.instance.manufacturer_address_entry_type == AddressEntryType.SEARCH:
                self.fields["manufacturer_address"].widget.attrs["readonly"] = True

            if self.instance.responsible_person_address_entry_type == AddressEntryType.SEARCH:
                self.fields["responsible_person_address"].widget.attrs["readonly"] = True

            # Contact isn't a field in the template.
            if "contact" in self.fields:
                self.fields["contact"].queryset = application_contacts(self.instance)

        # These are only sometimes required and will be checked in the clean method
        self.fields["auditor_accredited"].required = False
        self.fields["auditor_certified"].required = False


class EditGMPForm(OptionalFormMixin, EditGMPFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitGMPForm(EditGMPFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean(self) -> dict[str, Any]:
        cleaned_data: dict[str, Any] = super().clean()

        if not self.is_valid():
            return cleaned_data

        responsible_person = cleaned_data["is_responsible_person"]
        if responsible_person != YesNoChoices.yes:
            self.add_error(
                "is_responsible_person",
                "You must be the responsible person to submit this application",
            )

        # Check responsible person postcode matches country
        rp_postcode: str = cleaned_data["responsible_person_postcode"]
        rp_country: str = cleaned_data["responsible_person_country"]

        rp_is_ni_postcode = is_northern_ireland_postcode(rp_postcode)
        if rp_is_ni_postcode and rp_country == self.instance.CountryType.GB:
            self.add_error("responsible_person_postcode", "Postcode should not start with BT")

        elif not rp_is_ni_postcode and rp_country == self.instance.CountryType.NIR:
            self.add_error("responsible_person_postcode", "Postcode must start with BT")

        # Check manufacturer postcode matches country
        m_postcode: str = cleaned_data["manufacturer_postcode"]
        m_country: str = cleaned_data["manufacturer_country"]
        m_is_ni_postcode = is_northern_ireland_postcode(m_postcode)

        if m_is_ni_postcode and m_country == self.instance.CountryType.GB:
            self.add_error("manufacturer_postcode", "Postcode should not start with BT")

        elif not m_is_ni_postcode and m_country == self.instance.CountryType.NIR:
            self.add_error("manufacturer_postcode", "Postcode must start with BT")

        # Manufacturing certificates checks
        gmp_certificate_issued = cleaned_data["gmp_certificate_issued"]

        if gmp_certificate_issued == self.instance.CertificateTypes.ISO_22716:
            auditor_accredited: str = cleaned_data["auditor_accredited"]
            auditor_certified: str = cleaned_data["auditor_certified"]

            if not auditor_accredited:
                self.add_error("auditor_accredited", "This field is required")

            if not auditor_certified:
                self.add_error("auditor_certified", "This field is required")

            if auditor_accredited == YesNoChoices.no and auditor_certified == YesNoChoices.no:
                self.add_error(
                    "auditor_certified",
                    "The auditor or auditing body must have been accredited to"
                    " either ISO 17021 or ISO 17065. You are also required to"
                    " upload certification confirming this.",
                )

        return cleaned_data
