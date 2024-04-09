from collections.abc import Iterable
from typing import Any

import django_filters
from django import forms
from django.db.models import QuerySet

from web.domains.case.export.forms import (
    CFSActiveIngredientForm,
    CFSManufacturerDetailsForm,
    CFSProductForm,
    CFSProductTypeForm,
    EditCFScheduleForm,
    EditCFSForm,
    EditCOMForm,
    EditGMPForm,
)
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplicationTemplate,
    CertificateOfGoodManufacturingPracticeApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    CFSProductActiveIngredientTemplate,
    CFSProductTemplate,
    CFSProductTypeTemplate,
    CFSScheduleTemplate,
    ExportApplicationType,
    ProductLegislation,
)


class CATFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label="Template Name", lookup_expr="icontains")
    application_type = django_filters.ChoiceFilter(
        choices=ExportApplicationType.Types.choices,
        label="Application Type",
        empty_label="Any",
    )
    is_active = django_filters.ChoiceFilter(
        choices=((True, "Current"), (False, "Archived")),
        label="Status",
        empty_label="Any",
    )

    class Meta:
        model = CertificateApplicationTemplate
        fields = ("name", "application_type", "is_active")


class CreateCATForm(forms.ModelForm):
    class Meta:
        model = CertificateApplicationTemplate
        fields = ("application_type", "template_country", "name", "description", "sharing")
        widgets = {"description": forms.Textarea({"rows": 4})}

    class Media:
        js = ("web/js/pages/cat-form.js",)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        application_type = cleaned_data.get("application_type")

        # if application_type is not set template_country is not displayed.
        if not application_type:
            return cleaned_data

        if application_type == ExportApplicationType.Types.FREE_SALE:
            if not cleaned_data.get("template_country"):
                self.add_error("template_country", "You must enter this item")

        return cleaned_data

    @property
    def show_template_country(self) -> bool:
        return (
            self.is_bound
            and self.data.get("application_type") == ExportApplicationType.Types.FREE_SALE
        )


class EditCATForm(forms.ModelForm):
    class Meta:
        model = CertificateApplicationTemplate
        fields = ("template_country", "name", "description", "sharing")
        widgets = {"description": forms.Textarea({"rows": 4})}
        help_texts = {
            "template_country": (
                "Country where the goods will be exported from."
                " Changing this value will result in all schedule legislations being cleared from the template."
            ),
        }

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        if self.instance.application_type == ExportApplicationType.Types.FREE_SALE:
            if not cleaned_data.get("template_country"):
                self.add_error("template_country", "You must enter this item")

        return cleaned_data

    def save(self, commit: bool = True) -> CertificateApplicationTemplate:
        # Save the CertificateApplicationTemplate instance
        cat = super().save(commit=commit)

        # Remove existing legislations.
        if self.show_template_country and "template_country" in self.changed_data:
            for schedule in cat.cfs_template.schedules.all():
                schedule.legislations.all().delete()

        return cat

    @property
    def show_template_country(self) -> bool:
        return (
            self.instance
            and self.instance.application_type == ExportApplicationType.Types.FREE_SALE
        )


def copy_form_fields(form_fields: Iterable[str], *exclude: str) -> list[str]:
    """Return a copy of the supplied form fields excluding values in exclude"""

    return [f for f in form_fields if f not in exclude]


class CertificateOfManufactureApplicationTemplateForm(EditCOMForm):
    class Meta:
        fields = copy_form_fields(EditCOMForm.Meta.fields, "contact")
        help_texts = EditCOMForm.Meta.help_texts
        labels = EditCOMForm.Meta.labels
        widgets = EditCOMForm.Meta.widgets
        model = CertificateOfManufactureApplicationTemplate


class CertificateOfGoodManufacturingPracticeApplicationTemplateForm(EditGMPForm):
    class Meta:
        model = CertificateOfGoodManufacturingPracticeApplicationTemplate
        fields = copy_form_fields(EditGMPForm.Meta.fields, "contact")
        widgets = EditGMPForm.Meta.widgets


class CertificateOfFreeSaleApplicationTemplateForm(EditCFSForm):
    class Meta:
        model = CertificateOfFreeSaleApplicationTemplate
        fields = copy_form_fields(EditCFSForm.Meta.fields, "contact")
        widgets = EditCFSForm.Meta.widgets


class CFSScheduleTemplateForm(EditCFScheduleForm):
    class Meta:
        model = CFSScheduleTemplate
        fields = copy_form_fields(EditCFScheduleForm.Meta.fields)
        widgets = EditCFScheduleForm.Meta.widgets

    def get_legislations_queryset(self) -> QuerySet[ProductLegislation]:
        legislation_qs = ProductLegislation.objects.filter(is_active=True)

        if self.instance.application.template.is_ni_template:
            legislation_qs = legislation_qs.filter(ni_legislation=True)
        else:
            legislation_qs = legislation_qs.filter(gb_legislation=True)

        return legislation_qs


class CFSManufacturerDetailsTemplateForm(CFSManufacturerDetailsForm):
    class Meta:
        model = CFSScheduleTemplate
        fields = copy_form_fields(CFSManufacturerDetailsForm.Meta.fields)
        widgets = CFSManufacturerDetailsForm.Meta.widgets


class CFSProductTemplateForm(CFSProductForm):
    class Meta:
        model = CFSProductTemplate
        fields = copy_form_fields(CFSProductForm.Meta.fields)
        labels = {
            "product_name": "Product Name",
        }


class CFSProductTemplateFormSetBase(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index: int) -> dict[str, Any]:
        kwargs = super().get_form_kwargs(index)

        return kwargs | {"schedule": self.instance}


CFSProductTemplateFormSet = forms.inlineformset_factory(
    CFSScheduleTemplate,
    CFSProductTemplate,
    form=CFSProductTemplateForm,
    formset=CFSProductTemplateFormSetBase,
    extra=5,
)


class CFSProductTypeTemplateForm(CFSProductTypeForm):
    class Meta:
        model = CFSProductTypeTemplate
        fields = copy_form_fields(CFSProductTypeForm.Meta.fields)
        labels = {
            "product_type_number": "Product Type Number",
        }


class CFSProductTypeTemplateFormSetBase(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index: int) -> dict[str, Any]:
        kwargs = super().get_form_kwargs(index)

        return kwargs | {"product": self.instance}

    def clean(self):
        """Checks that no two product types have the same number."""

        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        product_types = set()

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            if pt := form.cleaned_data.get("product_type_number"):
                if pt in product_types:
                    form.add_error(
                        "product_type_number",
                        "Product type number must be unique to the product.",
                    )

                product_types.add(pt)


CFSProductTypeTemplateFormSet = forms.inlineformset_factory(
    CFSProductTemplate,
    CFSProductTypeTemplate,
    form=CFSProductTypeTemplateForm,
    formset=CFSProductTypeTemplateFormSetBase,
)


class CFSActiveIngredientTemplateForm(CFSActiveIngredientForm):
    class Meta:
        model = CFSProductActiveIngredientTemplate
        fields = copy_form_fields(CFSActiveIngredientForm.Meta.fields)


class CFSActiveIngredientTemplateFormSetBase(forms.BaseInlineFormSet):
    def get_form_kwargs(self, index: int) -> dict[str, Any]:
        kwargs = super().get_form_kwargs(index)

        return kwargs | {"product": self.instance}

    def clean(self):
        """Checks that no two active ingredients have the same CAS number."""

        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        cas_numbers = set()

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            if cn := form.cleaned_data.get("cas_number"):
                if cn in cas_numbers:
                    form.add_error("cas_number", "CAS number must be unique to the product.")

                cas_numbers.add(cn)


CFSActiveIngredientTemplateFormSet = forms.inlineformset_factory(
    CFSProductTemplate,
    CFSProductActiveIngredientTemplate,
    form=CFSActiveIngredientTemplateForm,
    formset=CFSActiveIngredientTemplateFormSetBase,
)
