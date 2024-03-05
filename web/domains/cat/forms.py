from collections.abc import Iterable

import django_filters
from django import forms

from web.domains.case.export.forms import (
    CFSManufacturerDetailsForm,
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
    CFSScheduleTemplate,
    ExportApplicationType,
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
        fields = ("application_type", "name", "description", "sharing")
        widgets = {"description": forms.Textarea({"rows": 4})}


class EditCATForm(forms.ModelForm):
    class Meta:
        model = CertificateApplicationTemplate
        fields = ("name", "description", "sharing")
        widgets = {"description": forms.Textarea({"rows": 4})}


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


class CFSManufacturerDetailsTemplateForm(CFSManufacturerDetailsForm):
    class Meta:
        model = CFSScheduleTemplate
        fields = copy_form_fields(CFSManufacturerDetailsForm.Meta.fields)
        widgets = CFSManufacturerDetailsForm.Meta.widgets
