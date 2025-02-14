from web.ecil.gds import forms as gds_forms
from web.models import User


class OneLoginNewUserUpdateForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = User
        fields = ("first_name", "last_name")
        labels = {
            "first_name": "First name",  # /PS-IGNORE
            "last_name": "Last name",  # /PS-IGNORE
        }
        error_messages = {
            "first_name": {"required": "Enter your first name"},  # /PS-IGNORE
            "last_name": {"required": "Enter your last name"},  # /PS-IGNORE
        }

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "first_name": {"classes": "govuk-!-width-two-thirds"},
                "last_name": {"classes": "govuk-!-width-two-thirds"},
            }
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for f in self.fields:
            self.fields[f].required = True


class ExporterTriageForm(gds_forms.GDSForm):
    applications = gds_forms.GovUKCheckboxesField(
        label="What are you applying for?",
        help_text="Select all that apply",
        error_messages={
            "required": "Select if you are applying for an export certificate or something else",
        },
        choices=[
            ("cfs", "Certificate of Free Sale (CFS)"),
            ("gmp", "Certificate of Good Manufacture Practice (CGMP)"),
            ("com", "Certificate of Manufacture (CoM)"),
            (gds_forms.GovUKCheckboxesField.NONE_OF_THESE, "Something else"),
        ],
        choice_hints={
            "cfs": "Products which meet UK standards that fall under Department for Business and Trade regulation.",
            "gmp": "Cosmetic products which meet UK good manufacturing practice standards. For use in China only.",
            "com": "Pesticides that are solely for use in overseas markets and will not be placed on the UK market.",
        },
        choice_classes="govuk-!-font-weight-bold",
        gds_field_kwargs={
            "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
        },
    )
