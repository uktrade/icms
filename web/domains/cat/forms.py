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
    EditCFSForm,
    EditCFSScheduleForm,
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


class CFSScheduleTemplateForm(EditCFSScheduleForm):
    class Meta:
        model = CFSScheduleTemplate
        fields = copy_form_fields(EditCFSScheduleForm.Meta.fields)
        widgets = EditCFSScheduleForm.Meta.widgets

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


class CFSProductTypeTemplateForm(CFSProductTypeForm):
    class Meta:
        model = CFSProductTypeTemplate
        fields = copy_form_fields(CFSProductTypeForm.Meta.fields)
        labels = {
            "product_type_number": "Product Type Number",
        }


class CFSActiveIngredientTemplateForm(CFSActiveIngredientForm):
    class Meta:
        model = CFSProductActiveIngredientTemplate
        fields = copy_form_fields(CFSActiveIngredientForm.Meta.fields)


# Example of how this works can be found here:
# https://micropyramid.com/blog/how-to-use-nested-formsets-in-django
class ManageCFSProductForm(CFSProductForm):
    class Meta:
        model = CFSProductTemplate
        fields = ("product_name",)
        labels = {"product_name": ""}


class ManageCFSActiveIngredientForm(CFSActiveIngredientForm):
    class Meta:
        model = CFSProductActiveIngredientTemplate
        fields = ("name", "cas_number")
        labels = {"name": "", "cas_number": ""}
        help_texts = {"cas_number": ""}


class ManageCFSProductTypeForm(CFSProductTypeForm):
    class Meta:
        model = CFSProductTypeTemplate
        fields = ("product_type_number",)
        labels = {"product_type_number": ""}


class BaseProductRelatedFormset(forms.BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields[forms.formsets.DELETION_FIELD_NAME].label = ""


# Used later on as nested formsets.
ActiveIngredientFormset = forms.inlineformset_factory(
    CFSProductTemplate,
    CFSProductActiveIngredientTemplate,
    form=ManageCFSActiveIngredientForm,
    formset=BaseProductRelatedFormset,
    extra=1,
)

ProductTypeFormset = forms.inlineformset_factory(
    CFSProductTemplate,
    CFSProductTypeTemplate,
    form=ManageCFSProductTypeForm,
    formset=BaseProductRelatedFormset,
    extra=1,
)


class BaseCFSProductFormset(forms.BaseInlineFormSet):
    def __init__(self, *args: Any, is_biocidal: bool, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.is_biocidal = is_biocidal

    def get_form_kwargs(self, index: int) -> dict[str, Any]:
        kwargs = super().get_form_kwargs(index)

        return kwargs | {"schedule": self.instance}

    def add_fields(self, form: ManageCFSProductForm, index: int) -> None:
        """Add custom fields to the CFS Product form.

        We add two nested formsets to each form in the product formset.
        """
        super().add_fields(form, index)
        form.fields[forms.formsets.DELETION_FIELD_NAME].label = ""

        # Do not add the extra form fields if not biocidal
        if not self.is_biocidal:
            return

        form.active_ingredient_formset = ActiveIngredientFormset(
            instance=form.instance,
            form_kwargs={"product": form.instance},
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None,
            prefix=f"active-ingredient-{form.prefix}-{ActiveIngredientFormset.get_default_prefix()}",
        )

        form.product_type_formset = ProductTypeFormset(
            instance=form.instance,
            form_kwargs={"product": form.instance},
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None,
            prefix=f"product-type-{form.prefix}-{ProductTypeFormset.get_default_prefix()}",
        )

    def is_valid(self) -> bool:
        result = super().is_valid()

        if self.is_bound:
            for form in self.forms:
                if hasattr(form, "active_ingredient_formset"):
                    result = result and form.active_ingredient_formset.is_valid()

                if hasattr(form, "product_type_formset"):
                    result = result and form.product_type_formset.is_valid()

        return result

    def save(
        self, commit: bool = True
    ) -> list[CFSProductTemplate | CFSProductActiveIngredientTemplate | CFSProductTypeTemplate]:
        """Return a list of saved and created objects."""
        result = super().save(commit=commit)

        for form in self.forms:
            if hasattr(form, "active_ingredient_formset"):
                if not self._should_delete_form(form):
                    ai_result = form.active_ingredient_formset.save(commit=commit)
                    if ai_result:
                        result.extend(ai_result)

            if hasattr(form, "product_type_formset"):
                if not self._should_delete_form(form):
                    pt_result = form.product_type_formset.save(commit=commit)
                    if pt_result:
                        result.extend(pt_result)

        return result


CFSProductTemplateFormset = forms.inlineformset_factory(
    CFSScheduleTemplate,
    CFSProductTemplate,
    form=ManageCFSProductForm,
    formset=BaseCFSProductFormset,
    extra=1,
)
