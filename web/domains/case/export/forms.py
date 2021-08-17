import re
from typing import Any, Optional

import structlog as logging
from django import forms
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django_select2.forms import ModelSelect2Widget, Select2MultipleWidget
from guardian.shortcuts import get_objects_for_user

from web.domains.case.forms import application_contacts
from web.domains.exporter.models import Exporter
from web.domains.file.utils import ICMSFileField
from web.domains.legislation.models import ProductLegislation
from web.domains.office.models import Office
from web.domains.user.models import User
from web.models.shared import YesNoChoices

from .models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSProduct,
    CFSProductActiveIngredient,
    CFSProductType,
    CFSSchedule,
)

logger = logging.get_logger(__name__)


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
            search_fields=("postcode__icontains", "address__icontains"),
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
            search_fields=("main_exporter__in", "exporter"),
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
            search_fields=("postcode__icontains", "address__icontains"),
            # Key is a name of a field in a form.
            # Value is a name of a field in a model (used in `queryset`).
            dependent_fields={"agent": "exporter"},
        ),
    )

    def __init__(self, *args: Any, user: User, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.user = user

        active_exporters = Exporter.objects.filter(is_active=True, main_exporter__isnull=True)
        exporters = get_objects_for_user(
            user,
            ["web.is_contact_of_exporter", "web.is_agent_of_exporter"],
            active_exporters,
            any_perm=True,
        )
        self.fields["exporter"].queryset = exporters
        self.fields["exporter_office"].queryset = Office.objects.filter(
            is_active=True, exporter__in=exporters
        )

        active_agents = Exporter.objects.filter(is_active=True, main_exporter__in=exporters)
        agents = get_objects_for_user(
            user,
            ["web.is_contact_of_exporter"],
            active_agents,
        )
        self.fields["agent"].queryset = agents
        self.fields["agent_office"].queryset = Office.objects.filter(
            is_active=True, exporter__in=agents
        )


class PrepareCertManufactureForm(forms.ModelForm):
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_pesticide_on_free_sale_uk"].required = True
        self.fields["is_manufacturer"].required = True

        self.fields["contact"].queryset = application_contacts(self.instance)

        application_countries = self.instance.application_type.country_group.countries.filter(
            is_active=True
        )
        self.fields["countries"].queryset = application_countries

    def clean_is_pesticide_on_free_sale_uk(self):
        val = self.cleaned_data["is_pesticide_on_free_sale_uk"]

        if val is None:
            raise forms.ValidationError("You must enter this item.")

        if val:
            raise forms.ValidationError(
                mark_safe(
                    """
                    <div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>

                    <p>A Certificate of Manufacture cannot be completed for a pesticide on free sale in the UK.</p>
                    <p>To process this request contact the following:</p>
                    <ul>
                      <li>Agricultural pesticides - <a href="mailto:asg@hse.gsi.gov.uk">asg@hse.gsi.gov.uk</a>
                      <li>Non-agricultural pesticides - <a href="mailto:biocidesenquiries@hse.gsi.gov.uk">biocidesenquiries@hse.gsi.gov.uk</a>
                    </ul>
                    </div>"""
                )
            )

        return val

    def clean_is_manufacturer(self):
        val = self.cleaned_data["is_manufacturer"]

        if val is None:
            raise forms.ValidationError("You must enter this item.")

        if not val:
            raise forms.ValidationError(
                mark_safe(
                    """
                    <div class="info-box info-box-danger"><div class="screen-reader-only">Warning information box,</div>

                    <p>A Certificate of Manufacture can only be applied for by the manufacturer of the pesticide.</p>
                    </div>"""
                )
            )

        return val


class EditCFSForm(forms.ModelForm):
    class Meta:
        model = CertificateOfFreeSaleApplication

        fields = (
            "contact",
            "countries",
        )

        widgets = {
            "countries": Select2MultipleWidget(
                attrs={"data-minimum-input-length": 0, "data-placeholder": "Select Country"},
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].queryset = application_contacts(self.instance)

        application_countries = self.instance.application_type.country_group.countries.filter(
            is_active=True
        )
        self.fields["countries"].queryset = application_countries


class EditCFScheduleForm(forms.ModelForm):
    class Meta:
        model = CFSSchedule
        fields = (
            "exporter_status",
            "brand_name_holder",
            "legislations",
            "product_eligibility",
            "goods_placed_on_uk_market",
            "goods_export_only",
            "any_raw_materials",
            "final_product_end_use",
            "country_of_manufacture",
            "schedule_statements",
        )

        widgets = {
            "legislations": Select2MultipleWidget(
                attrs={"data-minimum-input-length": 0, "data-placeholder": "Select Legislation"},
            )
        }

    def clean(self):
        cleaned_data: dict[str, Any] = super().clean()

        if not self.is_valid():
            return cleaned_data

        # Check any raw materials field
        any_raw_materials: str = cleaned_data["any_raw_materials"]
        final_product_end_use: Optional[str] = cleaned_data["final_product_end_use"]

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
        widgets = {"manufacturer_address": forms.Textarea}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            if self.instance.manufacturer_address_entry_type == CFSSchedule.AddressEntryType.SEARCH:
                self.fields["manufacturer_address"].widget.attrs["readonly"] = True


class CFSProductForm(forms.ModelForm):
    class Meta:
        model = CFSProduct
        fields = ("product_name",)

    def __init__(self, *args, schedule: CFSSchedule, **kwargs):
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


class CFSProductTypeForm(forms.ModelForm):
    class Meta:
        model = CFSProductType
        fields = ("product_type_number",)

    def __init__(self, *args, product: CFSProduct, **kwargs):
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

    def __init__(self, *args, product: CFSProduct, **kwargs):
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


class EditGMPForm(forms.ModelForm):
    class Meta:
        model = CertificateOfGoodManufacturingPracticeApplication

        fields = (
            "contact",
            "countries",
        )

        widgets = {
            "countries": Select2MultipleWidget(
                attrs={"data-minimum-input-length": 0, "data-placeholder": "Select Country"},
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].queryset = application_contacts(self.instance)

        application_countries = self.instance.application_type.country_group.countries.filter(
            is_active=True
        )
        self.fields["countries"].queryset = application_countries
