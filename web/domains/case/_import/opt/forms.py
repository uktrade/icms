import datetime

from django import forms

from web.domains.country.models import Country
from web.domains.user.models import User
from web.forms.widgets import DateInput
from web.models.shared import YesNoNAChoices

from . import models


class EditOPTForm(forms.ModelForm):
    # TODO: filter users here correctly (users with access to the importer)
    contact = forms.ModelChoiceField(
        queryset=User.objects.all(),
        help_text="Select the main point of contact for the case. This will usually be the person who created the application.",
    )

    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "contact",
            "applicant_reference",
            "customs_office_name",
            "customs_office_address",
            "rate_of_yield",
            "rate_of_yield_calc_method",
            "last_export_day",
            "reimport_period",
            "nature_process_ops",
            "suggested_id",
        )

        widgets = {
            "last_export_day": DateInput(),
            "customs_office_address": forms.Textarea({"rows": 4}),
            "rate_of_yield_calc_method": forms.Textarea({"rows": 2}),
            "nature_process_ops": forms.Textarea({"rows": 2}),
            "suggested_id": forms.Textarea({"rows": 2}),
        }

    def clean_last_export_day(self):
        day = self.cleaned_data["last_export_day"]

        if day <= datetime.date.today():
            raise forms.ValidationError("Date must be in the future.")

        return day


class CompensatingProductsOPTForm(forms.ModelForm):
    cp_origin_country = forms.ModelChoiceField(
        label="Country Of Origin",
        queryset=Country.objects.filter(country_groups__name="OPT COOs"),
        required=True,
        help_text="Select the country that the compensating products originate from.",
    )

    cp_processing_country = forms.ModelChoiceField(
        label="Country Of Processing",
        queryset=Country.objects.filter(country_groups__name="OPT COOs"),
        required=True,
        help_text="Select the country that the compensating products were processed in.",
    )

    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "cp_origin_country",
            "cp_processing_country",
            "cp_category",
            "cp_total_quantity",
            "cp_total_value",
        )


class FurtherQuestionsOPTForm(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_similar_to_own_factory",
            "fq_manufacturing_within_eu",
            "fq_maintained_in_eu",
            "fq_maintained_in_eu_reasons",
        )

        widgets = {
            "fq_maintained_in_eu_reasons": forms.Textarea({"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if (cleaned_data.get("fq_maintained_in_eu") == YesNoNAChoices.no) and not cleaned_data.get(
            "fq_maintained_in_eu_reasons"
        ):
            self.add_error(
                "fq_maintained_in_eu_reasons", forms.Field.default_error_messages["required"]
            )

        return cleaned_data


class SubmitOPTForm(forms.Form):
    confirmation = forms.CharField(
        label='Confirm that you agree to the above by typing "I AGREE", in capitals, in this box'
    )

    def clean_confirmation(self):
        confirmation = self.cleaned_data["confirmation"]

        if confirmation != "I AGREE":
            raise forms.ValidationError("Please agree to the declaration of truth.")

        return confirmation
