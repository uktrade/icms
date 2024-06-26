import datetime as dt
from typing import Any

from django import forms

import web.forms.widgets as icms_widgets
from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.domains.commodity.widgets import CommodityWidget
from web.forms.fields import JqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.models import Commodity, Country
from web.models.shared import YesNoChoices, YesNoNAChoices

from . import models
from .widgets import OptCompensatingProductsCommodityWidget


class OptFormBase(forms.ModelForm):
    last_export_day = JqueryDateField(
        required=True,
        label="Last Export Day",
        help_text="Requested last day of authorised exportation.",
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
            "customs_office_address": forms.Textarea({"rows": 4}),
            "rate_of_yield_calc_method": forms.Textarea({"rows": 2}),
            "nature_process_ops": forms.Textarea({"rows": 2}),
            "suggested_id": forms.Textarea({"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)


class EditOPTForm(OptionalFormMixin, OptFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitOptForm(OptFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean_last_export_day(self):
        day = self.cleaned_data["last_export_day"]

        if day <= dt.date.today():
            raise forms.ValidationError("Date must be in the future.")

        return day


class CompensatingProductsOPTFormBase(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "cp_origin_country",
            "cp_processing_country",
            "cp_category",
            "cp_total_quantity",
            "cp_total_value",
            "cp_commodities",
        )

        widgets = {
            "cp_commodities": OptCompensatingProductsCommodityWidget(
                attrs={
                    "data-minimum-input-length": 0,
                    "data-placeholder": "Please choose a commodity",
                },
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        opt_coo_countries = Country.app.get_opt_coo_countries()

        self.fields["cp_origin_country"].queryset = opt_coo_countries
        self.fields["cp_processing_country"].queryset = opt_coo_countries


class EditCompensatingProductsOPTForm(OptionalFormMixin, CompensatingProductsOPTFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitCompensatingProductsOPTForm(CompensatingProductsOPTFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean(self):
        """Validate commodities and category to ensure they match."""

        cleaned_data = super().clean()
        commodities = cleaned_data.get("cp_commodities")
        category = cleaned_data.get("cp_category")

        if not commodities or not category:
            return cleaned_data

        user_commodities = commodities.values_list("commodity_code", flat=True)

        valid_commodities = OptCompensatingProductsCommodityWidget.queryset.filter(
            commoditygroup__group_code=category
        ).values_list("commodity_code", flat=True)

        if any(commodity not in valid_commodities for commodity in user_commodities):
            self.add_error(
                "cp_commodities", f"Invalid commodity code selected for category {category}"
            )

        return cleaned_data


class TemporaryExportedGoodsOPTFormBase(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "teg_origin_country",
            "teg_total_quantity",
            "teg_total_value",
            "teg_goods_description",
            "teg_commodities",
        )

        widgets = {
            "teg_commodities": CommodityWidget(
                attrs={
                    "data-minimum-input-length": 1,
                    "data-placeholder": "Please choose a commodity",
                },
                queryset=Commodity.objects.filter(sigl_product_type="TEX"),
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["teg_origin_country"].queryset = Country.app.get_opt_temp_export_coo_countries()


class EditTemporaryExportedGoodsOPTForm(OptionalFormMixin, TemporaryExportedGoodsOPTFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitTemporaryExportedGoodsOPTForm(TemporaryExportedGoodsOPTFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """


class FurtherQuestionsOPTFormBase(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_similar_to_own_factory",
            "fq_manufacturing_within_eu",
            "fq_maintained_in_eu",
            "fq_maintained_in_eu_reasons",
        )

        widgets = {
            "fq_similar_to_own_factory": icms_widgets.RadioSelectInline,
            "fq_manufacturing_within_eu": icms_widgets.RadioSelectInline,
            "fq_maintained_in_eu": icms_widgets.RadioSelectInline,
            "fq_maintained_in_eu_reasons": forms.Textarea({"rows": 3}),
        }


class EditFurtherQuestionsOPTForm(OptionalFormMixin, FurtherQuestionsOPTFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitFurtherQuestionsOPTForm(FurtherQuestionsOPTFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean(self):
        cleaned_data = super().clean()

        if (cleaned_data.get("fq_maintained_in_eu") == YesNoNAChoices.no) and not cleaned_data.get(
            "fq_maintained_in_eu_reasons"
        ):
            self.add_error(
                "fq_maintained_in_eu_reasons", forms.Field.default_error_messages["required"]
            )

        return cleaned_data


class FurtherQuestionsBaseOPTForm(forms.ModelForm):
    def __init__(self, *args: Any, has_files: bool, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.has_files = has_files


class FurtherQuestionsEmploymentDecreasedOPTForm(FurtherQuestionsBaseOPTForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_employment_decreased",
            "fq_employment_decreased_reasons",
        )

        widgets = {
            "fq_employment_decreased": icms_widgets.RadioSelectInline,
            "fq_employment_decreased_reasons": forms.Textarea({"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if (
            (cleaned_data.get("fq_employment_decreased") == YesNoNAChoices.yes)
            and not cleaned_data.get("fq_employment_decreased_reasons")
            and not self.has_files
        ):
            self.add_error(
                "fq_employment_decreased_reasons", "You must enter this item, or attach a file"
            )

        return cleaned_data


class FurtherQuestionsPriorAuthorisationOPTForm(FurtherQuestionsBaseOPTForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_prior_authorisation",
            "fq_prior_authorisation_reasons",
        )

        widgets = {
            "fq_prior_authorisation": icms_widgets.RadioSelectInline,
            "fq_prior_authorisation_reasons": forms.Textarea({"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if (
            (cleaned_data.get("fq_prior_authorisation") == YesNoChoices.yes)
            and not cleaned_data.get("fq_prior_authorisation_reasons")
            and not self.has_files
        ):
            self.add_error(
                "fq_prior_authorisation_reasons", "You must enter this item, or attach a file"
            )

        return cleaned_data


class FurtherQuestionsPastBeneficiaryOPTForm(FurtherQuestionsBaseOPTForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_past_beneficiary",
            "fq_past_beneficiary_reasons",
        )

        widgets = {
            "fq_past_beneficiary": icms_widgets.RadioSelectInline,
            "fq_past_beneficiary_reasons": forms.Textarea({"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if (
            (cleaned_data.get("fq_past_beneficiary") == YesNoChoices.yes)
            and not cleaned_data.get("fq_past_beneficiary_reasons")
            and not self.has_files
        ):
            self.add_error(
                "fq_past_beneficiary_reasons", "You must enter this item, or attach a file"
            )

        return cleaned_data


class FurtherQuestionsNewApplicationOPTForm(FurtherQuestionsBaseOPTForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_new_application",
            "fq_new_application_reasons",
        )

        widgets = {
            "fq_new_application": icms_widgets.RadioSelectInline,
            "fq_new_application_reasons": forms.Textarea({"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if (
            (cleaned_data.get("fq_new_application") == YesNoChoices.yes)
            and not cleaned_data.get("fq_new_application_reasons")
            and not self.has_files
        ):
            self.add_error(
                "fq_new_application_reasons", "You must enter this item, or attach a file"
            )

        return cleaned_data


class FurtherQuestionsFurtherAuthorisationOPTForm(FurtherQuestionsBaseOPTForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = (
            "fq_further_authorisation",
            "fq_further_authorisation_reasons",
        )

        widgets = {
            "fq_further_authorisation": icms_widgets.RadioSelectInline,
            "fq_further_authorisation_reasons": forms.Textarea({"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if (
            (cleaned_data.get("fq_further_authorisation") == YesNoChoices.yes)
            and not cleaned_data.get("fq_further_authorisation_reasons")
            and not self.has_files
        ):
            self.add_error(
                "fq_further_authorisation_reasons", "You must enter this item, or attach a file"
            )

        return cleaned_data


class FurtherQuestionsSubcontractProductionOPTForm(FurtherQuestionsBaseOPTForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = ("fq_subcontract_production",)

        widgets = {"fq_subcontract_production": icms_widgets.RadioSelectInline}

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("fq_subcontract_production") == YesNoChoices.yes
        ) and not self.has_files:
            self.add_error(
                "fq_subcontract_production",
                "Please ensure you have uploaded a declaration from the subcontractor",
            )

        return cleaned_data


class OPTChecklistForm(ChecklistBaseForm):
    class Meta:
        model = models.OPTChecklist

        fields = (
            "operator_requests_submitted",
            "authority_to_issue",
        ) + tuple(f for f in ChecklistBaseForm.Meta.fields if f != "endorsements_listed")


class OPTChecklistOptionalForm(OPTChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class ResponsePrepCompensatingProductsOPTForm(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication

        fields = ("cp_total_quantity", "cp_total_value", "cp_category_licence_description")


class ResponsePrepTemporaryExportedGoodsOPTForm(forms.ModelForm):
    class Meta:
        model = models.OutwardProcessingTradeApplication
        fields = ("teg_total_quantity", "teg_total_value", "teg_goods_description")
