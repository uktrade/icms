from django import forms
from django_select2.forms import ModelSelect2Widget
from guardian.shortcuts import get_objects_for_user

from web.domains.case._import.models import (
    ImportApplicationType,
    OpenIndividualLicenceApplication,
    UserImportCertificate,
)
from web.domains.commodity.models import CommodityGroup, CommodityType
from web.domains.country.models import Country
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.forms.widgets import DateInput


class CreateOILForm(forms.ModelForm):
    importer = forms.ModelChoiceField(
        queryset=Importer.objects.none(),
        label="Main Importer",
        widget=ModelSelect2Widget(
            search_fields=(
                "name__icontains",
                "user__first_name__icontains",
                "user__last_name__icontains",
            )
        ),
    )
    importer_office = forms.ModelChoiceField(
        queryset=Office.objects.none(),
        label="Importer Office",
        widget=ModelSelect2Widget(
            search_fields=("postcode__icontains", "address__icontains"),
            dependent_fields={"importer": "importer"},
        ),
    )

    class Meta:
        model = OpenIndividualLicenceApplication
        fields = ("importer", "importer_office")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        active_importers = Importer.objects.filter(is_active=True)
        importers = get_objects_for_user(
            user,
            ["web.is_contact_of_importer", "web.is_agent_of_importer"],
            active_importers,
            any_perm=True,
            with_superuser=True,
        )
        self.fields["importer"].queryset = importers
        self.fields["importer_office"].queryset = Office.objects.filter(
            is_active=True, importer__in=importers
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        application_type = ImportApplicationType.objects.filter(
            is_active=True, sub_type=ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE
        ).first()
        instance.application_type = application_type
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PrepareOILForm(forms.ModelForm):
    applicant_reference = forms.CharField(
        label="Applicant's Reference", help_text="Enter your own reference for this application."
    )
    contact = forms.ModelChoiceField(
        queryset=User.objects.all(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )
    commodity_group = forms.ModelChoiceField(
        label="Commodity Code",
        queryset=CommodityGroup.objects.filter(
            is_active=True, commodity_type__type=CommodityType.FIREARMS_AND_AMMUNITION
        ),
        help_text="""
            You must pick the commodity code group that applies to the items that you wish to
            import. Please note that "ex Chapter 97" is only relevant to collectors pieces and
            items over 100 years old. Please contact HMRC classification advisory service,
            01702 366077, if you are unsure of the correct code.
        """,
    )
    origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        empty_label=None,
        queryset=Country.objects.filter(name="Any Country"),
    )
    consignment_country = forms.ModelChoiceField(
        label="Country Of Consignment",
        empty_label=None,
        queryset=Country.objects.filter(name="Any Country"),
    )
    section1 = forms.BooleanField(disabled=True, label="Firearms Licence for")
    section2 = forms.BooleanField(disabled=True, label="")

    class Meta:
        model = OpenIndividualLicenceApplication
        fields = (
            "contact",
            "applicant_reference",
            "section1",
            "section2",
            "origin_country",
            "consignment_country",
            "commodity_group",
            "know_bought_from",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True


class UserImportCertificateForm(forms.ModelForm):
    document = forms.FileField(required=False, widget=forms.ClearableFileInput())
    certificate_type = forms.ChoiceField(choices=(UserImportCertificate.REGISTERED,))

    class Meta:
        model = UserImportCertificate
        fields = (
            "reference",
            "certificate_type",
            "constabulary",
            "date_issued",
            "expiry_date",
            "document",
        )
        widgets = {"date_issued": DateInput, "expiry_date": DateInput}

    def clean(self):
        data = super().clean()

        # document is handled in the view
        data.pop("document", None)
