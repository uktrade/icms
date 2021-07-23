from django import forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.country.models import Country

from . import models


class PrepareOILForm(forms.ModelForm):
    commodity_code = forms.ChoiceField(
        label="Commodity Code",
        help_text="""
            You must pick the commodity code group that applies to the items that you wish to
            import. Please note that "ex Chapter 97" is only relevant to collectors pieces and
            items over 100 years old. Please contact HMRC classification advisory service,
            01702 366077, if you are unsure of the correct code.
        """,
        choices=[(x, x) for x in [None, "ex Chapter 93", "ex Chapter 95"]],
    )
    section1 = forms.BooleanField(disabled=True, label="Firearms Licence for")
    section2 = forms.BooleanField(disabled=True, label="")

    class Meta:
        model = models.OpenIndividualLicenceApplication
        fields = (
            "contact",
            "applicant_reference",
            "section1",
            "section2",
            "origin_country",
            "consignment_country",
            "commodity_code",
            "know_bought_from",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True

        self.fields["contact"].queryset = application_contacts(self.instance)

        # The default label for unknown is "Unknown"
        self.fields["know_bought_from"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        self.fields["origin_country"].empty_label = None
        self.fields["consignment_country"].empty_label = None

        countries = Country.objects.filter(name="Any Country")
        self.fields["origin_country"].queryset = countries
        self.fields["consignment_country"].queryset = countries


class ChecklistFirearmsOILApplicationForm(ChecklistBaseForm):
    class Meta:
        model = models.ChecklistFirearmsOILApplication

        fields = (
            "authority_required",
            "authority_received",
            "authority_police",
        ) + ChecklistBaseForm.Meta.fields

        labels = {
            "validity_period_correct": "Validity period of licence matches that of the RFD certificate?",
        }


class ChecklistFirearmsOILApplicationOptionalForm(ChecklistFirearmsOILApplicationForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False
