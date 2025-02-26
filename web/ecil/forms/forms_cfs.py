from web.ecil.gds import forms as gds_forms
from web.models import CertificateOfFreeSaleApplication


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
