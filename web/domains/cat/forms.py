from django import forms
from django_select2.forms import Select2MultipleWidget

from web.domains.case.export.models import ExportApplicationType
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
        required=False, choices=YesNoChoices.choices, widget=icms_widgets.RadioSelectInline
    )
    is_responsible_person = forms.ChoiceField(
        required=False, choices=YesNoChoices.choices, widget=icms_widgets.RadioSelectInline
    )
    manufacturer_address = forms.CharField(required=False, widget=forms.Textarea)
    manufacturer_address_entry_type = forms.ChoiceField(
        required=False, choices=AddressEntryType.choices, widget=icms_widgets.RadioSelectInline
    )
    manufacturer_country = forms.ChoiceField(required=False, widget=icms_widgets.RadioSelect)
    manufacturer_name = forms.CharField(required=False)
    manufacturer_postcode = forms.CharField(required=False)
    responsible_person_address = forms.CharField(required=False, widget=forms.Textarea)
    responsible_person_address_entry_type = forms.ChoiceField(
        required=False, choices=AddressEntryType.choices, widget=icms_widgets.RadioSelectInline
    )
    responsible_person_country = forms.CharField(required=False, widget=icms_widgets.RadioSelect)
    responsible_person_name = forms.CharField(required=False)
    responsible_person_postcode = forms.CharField(required=False)
    gmp_certificate_issued = forms.ChoiceField(required=False, widget=icms_widgets.RadioSelect)
    auditor_accredited = forms.ChoiceField(
        required=False, choices=YesNoChoices.choices, widget=icms_widgets.RadioSelectInline
    )
    auditor_certified = forms.ChoiceField(
        required=False, choices=YesNoChoices.choices, widget=icms_widgets.RadioSelectInline
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
