from django import forms
from django_select2.forms import Select2MultipleWidget

from web.domains.case.export.models import (
    CertificateOfGoodManufacturingPracticeApplication,
    ExportApplicationType,
)
from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.country.models import Country
from web.forms import widgets as icms_widgets
from web.models.shared import AddressEntryType, YesNoChoices


class SearchCATForm(forms.Form):
    template_name = forms.CharField()
    application_type = forms.ChoiceField(
        choices=[("any", "Any")] + ExportApplicationType.Types.choices
    )
    status = forms.ChoiceField(
        choices=(("any", "Any"), ("current", "Current"), ("archived", "Archived"))
    )


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


class GMPTemplateForm(forms.Form):
    # Good manufacturing practice. Similar to EditGMPForm.
    contact = forms.CharField(required=False)
    is_manufacturer = forms.ChoiceField(
        required=False,
        choices=YesNoChoices.choices,
        widget=icms_widgets.RadioSelectInline,
        label="Are you the manufacturer of the cosmetic products?",
    )
    is_responsible_person = forms.ChoiceField(
        required=False,
        choices=YesNoChoices.choices,
        widget=icms_widgets.RadioSelectInline,
        label="Are you the responsible person as defined by Cosmetic Products Legislation as applicable in GB or NI?",
    )
    manufacturer_address = forms.CharField(required=False, widget=forms.Textarea, label="Address")
    manufacturer_address_entry_type = forms.ChoiceField(
        required=False,
        choices=AddressEntryType.choices,
        widget=icms_widgets.RadioSelectInline,
        label="Address Type",
    )
    manufacturer_country = forms.ChoiceField(
        choices=CertificateOfGoodManufacturingPracticeApplication.CountryType.choices,
        required=False,
        widget=icms_widgets.RadioSelect,
        label="Country of Manufacture",
    )
    manufacturer_name = forms.CharField(required=False, label="Name")
    manufacturer_postcode = forms.CharField(required=False, label="Postcode")
    responsible_person_address = forms.CharField(
        required=False, widget=forms.Textarea, label="Address"
    )
    responsible_person_address_entry_type = forms.ChoiceField(
        required=False,
        choices=AddressEntryType.choices,
        widget=icms_widgets.RadioSelectInline,
        label="Address Type",
    )
    responsible_person_country = forms.ChoiceField(
        required=False,
        widget=icms_widgets.RadioSelect,
        choices=CertificateOfGoodManufacturingPracticeApplication.CountryType.choices,
        label="Country of Responsible Person",
    )
    responsible_person_name = forms.CharField(required=False, label="Name")
    responsible_person_postcode = forms.CharField(required=False, label="Postcode")
    gmp_certificate_issued = forms.ChoiceField(
        choices=CertificateOfGoodManufacturingPracticeApplication.CertificateTypes.choices,
        required=False,
        widget=icms_widgets.RadioSelect,
        label="Which valid certificate of Good Manufacturing Practice (GMP) has"
        " your cosmetics manufacturer been issued with?",
    )
    auditor_accredited = forms.ChoiceField(
        required=False,
        choices=YesNoChoices.choices,
        widget=icms_widgets.RadioSelectInline,
        label=(
            "Is the auditor or auditing body who inspected and certified the"
            " manufacturing facility accredited according to ISO 17021 by a"
            " national accreditation body which is a member of the"
            " International Accreditation Forum?"
        ),
    )
    auditor_certified = forms.ChoiceField(
        required=False,
        choices=YesNoChoices.choices,
        widget=icms_widgets.RadioSelectInline,
        label=(
            "Is the auditor or auditing body who inspected and certified the"
            " manufacturing facility accredited according to ISO 17065 by a"
            " national accreditation body which is a member of the"
            " International Accreditation Forum?"
        ),
    )


class COMTemplateForm(forms.Form):
    # Certificate of manufacture. Similar to PrepareCertManufactureForm form.
    countries = forms.ModelChoiceField(
        Country.objects.all(), required=False, widget=Select2MultipleWidget
    )
    is_pesticide_on_free_sale_uk = forms.BooleanField(
        required=False, label="Is the pesticide on free sale in the UK?"
    )
    is_manufacturer = forms.BooleanField(
        required=False, label="Is the applicant company the manufacturer of the pesticide?"
    )
    product_name = forms.CharField(required=False)
    chemical_name = forms.CharField(required=False)
    manufacturing_process = forms.CharField(
        required=False, widget=forms.Textarea, help_text="Please provide an outline of the process."
    )


class CFSTemplateForm(forms.Form):
    # Certificate of free sale. Similar to EditCFSForm form.
    countries = forms.ModelChoiceField(
        Country.objects.all(), required=False, widget=Select2MultipleWidget
    )
