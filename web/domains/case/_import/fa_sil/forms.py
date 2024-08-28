from typing import Any

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django_select2 import forms as s2forms

from web.domains.case._import.forms import ChecklistBaseForm
from web.domains.case.forms import application_contacts
from web.forms.fields import PastOnlyJqueryDateField
from web.forms.mixins import OptionalFormMixin
from web.forms.widgets import YesNoRadioSelectInline
from web.models import Country, ObsoleteCalibre, Template

from . import models
from .widgets import Section5ClauseSelect


class FirearmSILFormBase(forms.ModelForm):
    additional_comments = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = models.SILApplication
        fields = (
            "contact",
            "applicant_reference",
            "section1",
            "section2",
            "section5",
            "section58_obsolete",
            "section58_other",
            "other_description",
            "origin_country",
            "consignment_country",
            "military_police",
            "eu_single_market",
            "manufactured",
            "commodity_code",
            "additional_comments",
        )

        widgets = {
            "military_police": YesNoRadioSelectInline,
            "eu_single_market": YesNoRadioSelectInline,
            "manufactured": YesNoRadioSelectInline,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["contact"].queryset = application_contacts(self.instance)

        self.fields["origin_country"].queryset = Country.app.get_fa_sil_coo_countries()
        self.fields["consignment_country"].queryset = Country.app.get_fa_sil_coc_countries()

        # Bool fields are optional by default
        for f in ["military_police", "eu_single_market", "manufactured"]:
            self.fields[f].required = True

    def clean_other_description(self):
        section58_other = self.cleaned_data["section58_other"]
        other_description = self.cleaned_data["other_description"]

        if section58_other and not other_description:
            raise forms.ValidationError("This field is required.")

        return other_description


class EditFaSILForm(OptionalFormMixin, FirearmSILFormBase):
    """Form used when editing the application.

    All fields are optional to allow partial record saving.
    """


class SubmitFaSILForm(FirearmSILFormBase):
    """Form used when submitting the application.

    All fields are fully validated to ensure form is correct.
    """

    def clean(self):
        cleaned_data = super().clean()

        # At least one section should be selected
        licence_for = ["section1", "section2", "section5", "section58_obsolete", "section58_other"]
        sections = (cleaned_data.get(section) for section in licence_for)

        if not any(sections):
            self.add_error("section1", "You must select at least one 'section'")
            self.add_error("section2", "You must select at least one 'section'")
            self.add_error("section5", "You must select at least one 'section'")
            self.add_error("section58_obsolete", "You must select at least one 'section'")
            self.add_error("section58_other", "You must select at least one 'section'")

        if cleaned_data.get("section58_other") and not cleaned_data.get("other_description"):
            self.add_error("other_description", "You must enter this item")


class SILGoodsSection1Form(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection1
        fields = ("manufacture", "description", "quantity", "unlimited_quantity")
        widgets = {
            "manufacture": YesNoRadioSelectInline,
            "description": forms.Textarea({"rows": 3}),
        }

    quantity = forms.IntegerField(max_value=settings.CHIEF_MAX_QUANTITY, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacture"].required = True

    def clean_manufacture(self):
        manufactured_before_1900 = self.cleaned_data["manufacture"]
        if manufactured_before_1900:
            raise forms.ValidationError(
                "If your firearm was manufactured before 1900 then an import licence is not required."
            )

        return manufactured_before_1900

    def clean(self):
        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        unlimited_quantity = cleaned_data.get("unlimited_quantity")

        if not quantity and not unlimited_quantity:
            self.add_error(
                "quantity", "You must enter either a quantity or select unlimited quantity"
            )

        if unlimited_quantity:
            cleaned_data["quantity"] = None


class SILGoodsSection2Form(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection2
        fields = ("manufacture", "description", "quantity", "unlimited_quantity")
        widgets = {
            "manufacture": YesNoRadioSelectInline,
            "description": forms.Textarea({"rows": 3}),
        }

    quantity = forms.IntegerField(max_value=settings.CHIEF_MAX_QUANTITY, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacture"].required = True

    def clean_manufacture(self):
        manufactured_before_1900 = self.cleaned_data["manufacture"]
        if manufactured_before_1900:
            raise forms.ValidationError(
                "If your firearm was manufactured before 1900 then an import licence is not required."
            )

        return manufactured_before_1900

    def clean(self):
        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        unlimited_quantity = cleaned_data.get("unlimited_quantity")

        if not quantity and not unlimited_quantity:
            self.add_error(
                "quantity", "You must enter either a quantity or select unlimited quantity"
            )

        if unlimited_quantity:
            cleaned_data["quantity"] = None


class SILGoodsSection5Form(forms.ModelForm):
    class Meta:
        model = models.SILGoodsSection5
        fields = (
            "section_5_clause",
            "manufacture",
            "description",
            "quantity",
            "unlimited_quantity",
        )
        widgets = {
            "section_5_clause": Section5ClauseSelect,
            "manufacture": YesNoRadioSelectInline,
            "description": forms.Textarea({"rows": 3}),
        }

    quantity = forms.IntegerField(max_value=settings.CHIEF_MAX_QUANTITY, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacture"].required = True

    def clean_manufacture(self):
        manufactured_before_1900 = self.cleaned_data["manufacture"]
        if manufactured_before_1900:
            raise forms.ValidationError(
                "If your firearm was manufactured before 1900 then an import licence is not required."
            )

        return manufactured_before_1900

    def clean(self):
        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        unlimited_quantity = cleaned_data.get("unlimited_quantity")

        if not quantity and not unlimited_quantity:
            self.add_error(
                "quantity", "You must enter either a quantity or select unlimited quantity"
            )

        if unlimited_quantity:
            cleaned_data["quantity"] = None


class SILGoodsSection582ObsoleteForm(forms.ModelForm):  # /PS-IGNORE
    obsolete_calibre = forms.ChoiceField(
        label="Obsolete Calibre", choices=(), widget=s2forms.Select2Widget
    )

    class Meta:
        model = models.SILGoodsSection582Obsolete  # /PS-IGNORE
        fields = (
            "curiosity_ornament",
            "acknowledgement",
            "centrefire",
            "manufacture",
            "original_chambering",
            "obsolete_calibre",
            "description",
            "quantity",
        )
        widgets = {
            "curiosity_ornament": YesNoRadioSelectInline,
            "centrefire": YesNoRadioSelectInline,
            "manufacture": YesNoRadioSelectInline,
            "original_chambering": YesNoRadioSelectInline,
            "description": forms.Textarea({"rows": 3}),
            "obsolete_calibre": s2forms.Select2Widget,
        }

    quantity = forms.IntegerField(max_value=settings.CHIEF_MAX_QUANTITY)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curiosity_ornament"].required = True
        self.fields["centrefire"].required = True
        self.fields["manufacture"].required = True
        self.fields["original_chambering"].required = True

        calibres = ObsoleteCalibre.objects.filter(is_active=True).order_by("calibre_group", "name")

        self.fields["obsolete_calibre"].choices = [("", "---------")] + [
            (calibre.name, calibre.name) for calibre in calibres
        ]

    def clean_curiosity_ornament(self):
        curiosity_ornament = self.cleaned_data["curiosity_ornament"]
        if curiosity_ornament is False:
            raise forms.ValidationError(
                'If you do not intend to possess the firearm as a "curiosity or ornament" you'
                " cannot choose Section 58(2). You must change your selection to either"
                " Section 1, Section 2 or Section 5."
            )

        return curiosity_ornament

    def clean_acknowledgement(self):
        acknowledgement = self.cleaned_data["acknowledgement"]
        if not acknowledgement:
            raise forms.ValidationError("You must acknowledge the above statement")

        return acknowledgement

    def clean_manufacture(self):
        manufacture = self.cleaned_data["manufacture"]
        if manufacture is False:
            message = mark_safe(
                "If your firearm was manufactured after 1939 then you cannot choose Section 58(2)"
                " and must change your selection to either Section 1, Section 2 or Section 5."
                "<br/>If your firearm was manufactured before 1900 then an import licence is not"
                " required."
            )
            raise forms.ValidationError(message)

        return manufacture

    def clean_centrefire(self):
        centrefire = self.cleaned_data["centrefire"]
        if not centrefire:
            raise forms.ValidationError(
                "If your firearm is not a breech loading centrefire firearm, you cannot choose"
                " Section 58(2) - Obsolete Calibre. You must change your selection to either"
                " Section 1, Section 2 or Section 5."
            )

        return centrefire

    def clean_original_chambering(self):
        original_chambering = self.cleaned_data["original_chambering"]
        if not original_chambering:
            raise forms.ValidationError(
                "If your item does not retain its original chambering you cannot choose Obsolete Calibre."
            )

        return original_chambering


class SILGoodsSection582OtherForm(forms.ModelForm):  # /PS-IGNORE
    class Meta:
        model = models.SILGoodsSection582Other  # /PS-IGNORE
        fields = (
            "curiosity_ornament",
            "acknowledgement",
            "manufacture",
            "description",
            "quantity",
            "muzzle_loading",
            "rimfire",
            "rimfire_details",
            "ignition",
            "ignition_details",
            "ignition_other",
            "chamber",
            "bore",
            "bore_details",
        )
        widgets = {
            "curiosity_ornament": YesNoRadioSelectInline,
            "manufacture": YesNoRadioSelectInline,
            "muzzle_loading": YesNoRadioSelectInline,
            "rimfire": YesNoRadioSelectInline,
            "ignition": YesNoRadioSelectInline,
            "chamber": YesNoRadioSelectInline,
            "bore": YesNoRadioSelectInline,
            "description": forms.Textarea({"rows": 3}),
        }

    quantity = forms.IntegerField(max_value=settings.CHIEF_MAX_QUANTITY)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curiosity_ornament"].required = True
        self.fields["manufacture"].required = True
        self.fields["muzzle_loading"].required = True
        self.fields["rimfire"].required = True
        self.fields["ignition"].required = True
        self.fields["chamber"].required = True
        self.fields["bore"].required = True

    def clean_curiosity_ornament(self):
        curiosity_ornament = self.cleaned_data["curiosity_ornament"]
        if curiosity_ornament is False:
            raise forms.ValidationError(
                'If you do not intend to possess the firearm as a "curiosity or ornament" you'
                " cannot choose Section 58(2). You must change your selection to either"
                " Section 1, Section 2 or Section 5."
            )

        return curiosity_ornament

    def clean_acknowledgement(self):
        acknowledgement = self.cleaned_data["acknowledgement"]
        if not acknowledgement:
            raise forms.ValidationError("You must acknowledge the above statement")

        return acknowledgement

    def clean_manufacture(self):
        manufacture = self.cleaned_data["manufacture"]
        if manufacture is False:
            message = mark_safe(
                "If your firearm was manufactured after 1939 then you cannot choose Section 58(2)"
                " and must change your selection to either Section 1, Section 2 or Section 5."
                "<br/>If your firearm was manufactured before 1900 then an import licence is not"
                " required."
            )
            raise forms.ValidationError(message)

        return manufacture

    def clean(self):
        cleaned_data = super().clean()

        muzzle_loading = cleaned_data.get("muzzle_loading", False)
        rimfire = cleaned_data.get("rimfire", False)
        ignition = cleaned_data.get("ignition", False)
        chamber = cleaned_data.get("chamber", False)
        bore = cleaned_data.get("bore", False)

        last_questions = (muzzle_loading, rimfire, ignition, chamber, bore)
        if not any(last_questions):
            message = (
                "If your answer is 'No' to each of the previous five Yes/No questions, then you"
                " cannot choose 'Section 58(2) - Other'. You must change your selection to either"
                " Section 1, Section 2 or Section 5."
            )
            self.add_error("bore", message)

        if last_questions.count(True) > 1:
            self.add_error(
                "bore", "Only one of the above five questions can be answered with 'Yes'"
            )

        if rimfire and not cleaned_data.get("rimfire_details"):
            self.add_error("rimfire_details", "You must enter this item")

        ignition_details = cleaned_data.get("ignition_details")
        if ignition and not ignition_details:
            self.add_error("ignition_details", "You must enter this item")

        if (
            ignition
            and ignition_details
            == models.SILGoodsSection582Other.IgnitionDetail.OTHER  # /PS-IGNORE
            and not cleaned_data.get("ignition_other")
        ):
            self.add_error("ignition_other", "You must enter this item")

        if bore and not cleaned_data.get("bore_details"):
            self.add_error("bore_details", "You must enter this item")


class SILChecklistForm(ChecklistBaseForm):
    class Meta:
        model = models.SILChecklist

        fields = (
            "authority_required",
            "authority_received",
            "authority_cover_items_listed",
            "quantities_within_authority_restrictions",
            "authority_police",
        ) + ChecklistBaseForm.Meta.fields


class SILChecklistOptionalForm(SILChecklistForm):
    """Used to enable partial saving of checklist."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = False


class ResponsePrepBaseForm(forms.ModelForm):
    """Base class form for editing description and quantity in the response preparation screen"""

    class Meta:
        fields = ("description", "quantity")

    quantity = forms.IntegerField(max_value=settings.CHIEF_MAX_QUANTITY)


class ResponsePrepUnlimitedBaseForm(ResponsePrepBaseForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if self.instance.unlimited_quantity:
            self.fields["quantity"].required = False
            self.fields["quantity"].widget = forms.NumberInput(attrs={"placeholder": "Unlimited"})
            self.fields["quantity"].disabled = True

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        unlimited_quantity = self.instance.unlimited_quantity

        if unlimited_quantity:
            cleaned_data["quantity"] = None

        return cleaned_data


class ResponsePrepSILGoodsSection1Form(ResponsePrepUnlimitedBaseForm):
    class Meta:
        model = models.SILGoodsSection1
        fields = ResponsePrepUnlimitedBaseForm.Meta.fields


class ResponsePrepSILGoodsSection2Form(ResponsePrepUnlimitedBaseForm):
    class Meta:
        model = models.SILGoodsSection2
        fields = ResponsePrepUnlimitedBaseForm.Meta.fields


class ResponsePrepSILGoodsSection5Form(ResponsePrepUnlimitedBaseForm):
    class Meta:
        model = models.SILGoodsSection5
        fields = ResponsePrepUnlimitedBaseForm.Meta.fields


class ResponsePrepSILGoodsSection582ObsoleteForm(ResponsePrepBaseForm):  # /PS-IGNORE
    class Meta:
        model = models.SILGoodsSection582Obsolete  # /PS-IGNORE
        fields = ResponsePrepBaseForm.Meta.fields


class ResponsePrepSILGoodsSection582OtherForm(ResponsePrepBaseForm):  # /PS-IGNORE
    class Meta:
        model = models.SILGoodsSection582Other  # /PS-IGNORE
        fields = ResponsePrepBaseForm.Meta.fields


class SILCoverLetterTemplateForm(forms.Form):
    template = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sil_cover_letters = [
            Template.Codes.COVER_FIREARMS_DEACTIVATED_FIREARMS,
            Template.Codes.COVER_FIREARMS_SIIL,
        ]
        self.fields["template"].queryset = Template.objects.filter(
            template_code__in=sil_cover_letters
        )


class SILSupplementaryInfoForm(forms.ModelForm):
    class Meta:
        model = models.SILSupplementaryInfo
        fields = ("no_report_reason",)
        widgets = {"no_report_reason": forms.Textarea({"rows": 3})}

    def __init__(self, *args: Any, application: models.SILApplication, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.application = application

        if not self.instance.reports.exists():
            self.fields["no_report_reason"].required = True

    def clean(self) -> dict[str, Any]:
        if self.application.importcontact_set.exists() and not self.instance.reports.exists():
            msg = (
                "You must provide the details of who you bought the items from and one or more"
                " firearms reports before you can complete reporting. Each report must include the"
                " means of transport, the date the firearms were received and the details of who"
                " you bought the items from."
            )

            self.add_error(None, msg)

        return super().clean()


class SILSupplementaryReportForm(forms.ModelForm):
    date_received = PastOnlyJqueryDateField(
        required=True, label="Date Received", year_select_range=6
    )

    class Meta:
        model = models.SILSupplementaryReport
        fields = ("transport", "date_received", "bought_from")

    def __init__(self, *args: Any, application: models.SILApplication, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.application = application
        self.fields["bought_from"].queryset = self.application.importcontact_set.all()

    def clean(self) -> dict[str, Any]:
        """Check all goods in the application have been included in the report"""

        cleaned_data = super().clean()

        # Return cleaned data if creating a new model instance
        if not self.instance.pk:
            return cleaned_data

        sections = [
            self.application.goods_section1,
            self.application.goods_section2,
            self.application.goods_section5,
            self.application.goods_section582_obsoletes,
            self.application.goods_section582_others,
        ]

        if any(
            section.filter(is_active=True)
            .exclude(supplementary_report_firearms__report=self.instance)
            .exists()
            for section in sections
        ):
            self.add_error(None, "You must enter this item.")

        return cleaned_data
