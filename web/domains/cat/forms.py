import django_filters
from django import forms

from web.domains.case.export.forms import PrepareCertManufactureFormBase
from web.forms.mixins import OptionalFormMixin
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
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


class CertificateOfManufactureTemplateForm(OptionalFormMixin, PrepareCertManufactureFormBase):
    class Meta:
        fields = [f for f in PrepareCertManufactureFormBase.Meta.fields if f != "contact"]
        help_texts = PrepareCertManufactureFormBase.Meta.help_texts
        labels = PrepareCertManufactureFormBase.Meta.labels
        widgets = PrepareCertManufactureFormBase.Meta.widgets

        model = CertificateOfManufactureApplicationTemplate
