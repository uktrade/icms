from typing import Any, Literal

from web.domains.case.forms import application_contacts
from web.ecil.gds import forms as gds_forms
from web.models import CertificateOfFreeSaleApplication, User


class CFSApplicationReferenceForm(gds_forms.GDSModelForm):
    class Meta(gds_forms.GDSModelForm.Meta):
        model = CertificateOfFreeSaleApplication
        fields = ["applicant_reference"]
        error_messages = {"applicant_reference": {"required": "Enter a name for the application"}}

        formfield_callback = gds_forms.GDSFormfieldCallback(
            gds_field_kwargs={
                "applicant_reference": {
                    "label": {"isPageHeading": True, "classes": "govuk-label--l"}
                }
            }
        )


class CFSApplicationContactForm(gds_forms.GDSForm):
    contact = gds_forms.GovUKRadioInputField(
        label="Who is the main contact for your application?",
        help_text="This would normally be the person who created the application",
        error_messages={"required": "Select the main contact for your application"},
        gds_field_kwargs={
            "fieldset": {"legend": {"isPageHeading": True, "classes": "govuk-fieldset__legend--l"}}
        },
    )

    def clean_contact(self) -> Literal["none-of-these"] | User:
        contact_pk = self.cleaned_data["contact"]

        if contact_pk == gds_forms.GovUKRadioInputField.NONE_OF_THESE:
            return contact_pk

        return self.contacts.get(pk=contact_pk)

    def __init__(
        self, *args: Any, instance: CertificateOfFreeSaleApplication, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.instance = instance

        self.contacts = application_contacts(self.instance)
        contact_list = [(c.pk, c.full_name) for c in self.contacts]
        contact_list.append((gds_forms.GovUKRadioInputField.NONE_OF_THESE, "Someone else"))

        self.fields["contact"].choices = contact_list
        if self.instance.contact:
            self.fields["contact"].initial = self.instance.contact.pk
