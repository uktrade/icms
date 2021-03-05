import datetime

from django import forms

from web.domains.user.models import User

from . import models


def _get_year_selection():
    """Get year selection for wood quota applications. These show last year and
    11 future years."""

    last_year = datetime.date.today().year - 1

    return range(last_year, last_year + 12)


class PrepareWoodQuotaForm(forms.ModelForm):
    applicant_reference = forms.CharField(
        label="Applicant's Reference",
        help_text="Enter your own reference for this application.",
        required=False,
    )

    # TODO: filter users here correctly (users with access to the importer)
    contact = forms.ModelChoiceField(
        queryset=User.objects.all(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )

    shipping_year = forms.IntegerField(
        help_text="""Year of shipment should normally be that shown on any
        export licence or other export authorisation from the exporting country
        covered by this application. Shipment is considered to have taken place
        when the goods are loaded onto the exporting aircraft, vehicle or
        vessel.""",
        widget=forms.Select(choices=[(x, x) for x in _get_year_selection()]),
    )

    exporter_address = forms.CharField(label="Exporter address", widget=forms.Textarea())

    exporter_vat_nr = forms.CharField(label="Exporter VAT number")

    class Meta:
        model = models.WoodQuotaApplication
        fields = (
            "contact",
            "applicant_reference",
            "shipping_year",
            "exporter_name",
            "exporter_address",
            "exporter_vat_nr",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
