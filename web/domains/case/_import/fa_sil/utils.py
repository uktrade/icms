from typing import NamedTuple

from django import forms as django_forms
from django.forms.models import model_to_dict, modelform_factory
from django.urls import reverse

from web.domains.case._import.fa.forms import (
    ImportContactKnowBoughtFromForm,
    UserImportCertificateForm,
)
from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.file.utils import ICMSFileField
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from . import forms, models, types


class CreateSILSectionConfig(NamedTuple):
    model_class: types.GoodsModelT
    form_class: types.GoodsFormT
    template: str


class ResponsePrepEditSILSectionConfig(NamedTuple):
    model_class: types.GoodsModelT
    form_class: types.ResponsePrepGoodsFormT


def _get_report_firearm_model(sil_section_type: str) -> types.SILReportFirearmModelT:
    if sil_section_type == "section1":
        return models.SILSupplementaryReportFirearmSection1

    elif sil_section_type == "section2":
        return models.SILSupplementaryReportFirearmSection2

    elif sil_section_type == "section5":
        return models.SILSupplementaryReportFirearmSection5

    elif sil_section_type == "section582-obsolete":
        return models.SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE

    elif sil_section_type == "section582-other":
        return models.SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE

    elif sil_section_type == "section_legacy":
        return models.SILSupplementaryReportFirearmSectionLegacy

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_report_firearm_form_class(sil_section_type: str) -> type[django_forms.ModelForm]:
    """Dynamically creates and returns a Form class for providing a SIIL Supplementary Report depending on the section.

    The resulting class looks something like the below:

    class SILSupplementaryReportFirearmSection1Form(forms.ModelForm):
        class Meta:
            model = models.SILSupplementaryReportFirearmSection1
            fields = ("serial_number", "calibre", "model", "proofing")
    """
    model_class = _get_report_firearm_model(sil_section_type)

    return modelform_factory(
        model_class,
        fields=("serial_number", "calibre", "model", "proofing"),
    )


def _get_report_upload_firearm_form_class(
    sil_section_type: str,
) -> type[django_forms.ModelForm]:
    """Dynamically creates and returns a Form class for uploading a SIIL firearm report.

    The resulting class looks something like the below:

    class SILSupplementaryReportUploadFirearmSection1Form(forms.ModelForm):
        file = ICMSFileField(required=True)

        class Meta:
            model = models.SILSupplementaryReportFirearmSection1
            fields = ("file")
    """
    model_class = _get_report_firearm_model(sil_section_type)

    class FileForm(django_forms.ModelForm):
        file = ICMSFileField(required=True)

    return modelform_factory(model_class, form=FileForm, fields=["file"])


def _get_sil_section_app_config(sil_section_type: str) -> CreateSILSectionConfig:
    if sil_section_type == "section1":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection1,
            form_class=forms.SILGoodsSection1Form,
            template="web/domains/case/import/fa-sil/goods/section1.html",
        )

    elif sil_section_type == "section2":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection2,
            form_class=forms.SILGoodsSection2Form,
            template="web/domains/case/import/fa-sil/goods/section2.html",
        )

    elif sil_section_type == "section5":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection5,
            form_class=forms.SILGoodsSection5Form,
            template="web/domains/case/import/fa-sil/goods/section5.html",
        )

    elif sil_section_type == "section582-obsolete":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Obsolete,  # /PS-IGNORE
            form_class=forms.SILGoodsSection582ObsoleteForm,  # /PS-IGNORE
            template="web/domains/case/import/fa-sil/goods/section582-obsolete.html",
        )

    elif sil_section_type == "section582-other":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Other,  # /PS-IGNORE
            form_class=forms.SILGoodsSection582OtherForm,  # /PS-IGNORE
            template="web/domains/case/import/fa-sil/goods/section582-other.html",
        )

    elif sil_section_type == "section_legacy":
        return CreateSILSectionConfig(
            model_class=models.SILLegacyGoods,
            # These are invalid, but we don't want to be able to edit them
            form_class=None,  # type: ignore[arg-type]
            template=None,  # type: ignore[arg-type]
        )

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_sil_section_resp_prep_config(sil_section_type: str) -> ResponsePrepEditSILSectionConfig:
    if sil_section_type == "section1":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection1,
            form_class=forms.ResponsePrepSILGoodsSection1Form,
        )

    elif sil_section_type == "section2":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection2,
            form_class=forms.ResponsePrepSILGoodsSection2Form,
        )

    elif sil_section_type == "section5":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection5,
            form_class=forms.ResponsePrepSILGoodsSection5Form,
        )

    elif sil_section_type == "section582-obsolete":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection582Obsolete,  # /PS-IGNORE
            form_class=forms.ResponsePrepSILGoodsSection582ObsoleteForm,  # /PS-IGNORE
        )

    elif sil_section_type == "section582-other":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection582Other,  # /PS-IGNORE
            form_class=forms.ResponsePrepSILGoodsSection582OtherForm,  # /PS-IGNORE
        )

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_sil_errors(application: models.SILApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    edit_url = reverse("import:fa-sil:edit", kwargs={"application_pk": application.pk})
    edit_url = f"{edit_url}?validate"

    # Check main form
    application_details_errors = PageErrors(page_name="Application Details", url=edit_url)
    application_form = forms.SubmitFaSILForm(data=model_to_dict(application), instance=application)
    create_page_errors(application_form, application_details_errors)

    # Check know bought from
    bought_from_errors = PageErrors(
        page_name="Details of who bought from",
        url=reverse("import:fa:manage-import-contacts", kwargs={"application_pk": application.pk}),
    )

    kbf_form = ImportContactKnowBoughtFromForm(
        data={"know_bought_from": application.know_bought_from}, application=application
    )
    create_page_errors(kbf_form, bought_from_errors)

    if application.know_bought_from and not application.importcontact_set.exists():
        bought_from_errors.add(
            FieldError(field_name="Person", messages=["At least one person must be added"])
        )

    errors.add(bought_from_errors)

    # Goods validation
    has_section1_goods = application.goods_section1.filter(is_active=True).exists()
    has_section2_goods = application.goods_section2.filter(is_active=True).exists()
    has_section5_goods = application.goods_section5.filter(is_active=True).exists()
    has_section58_obsolete_goods = application.goods_section582_obsoletes.filter(
        is_active=True
    ).exists()
    has_section58_other_goods = application.goods_section582_others.filter(is_active=True).exists()

    if application.section1 and not has_section1_goods:
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section1"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 1", url=url)
        section_errors.add(
            FieldError(field_name="Goods", messages=["At least one 'section 1' must be added"])
        )
        errors.add(section_errors)

    if application.section2 and not has_section2_goods:
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section2"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 2", url=url)
        section_errors.add(
            FieldError(field_name="Goods", messages=["At least one 'section 2' must be added"])
        )
        errors.add(section_errors)

    if application.section5 and not has_section5_goods:
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section5"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 5", url=url)
        section_errors.add(
            FieldError(field_name="Goods", messages=["At least one 'section 5' must be added"])
        )
        errors.add(section_errors)

    if application.section58_obsolete and not has_section58_obsolete_goods:
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section582-obsolete"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 58(2) - Obsolete", url=url)
        section_errors.add(
            FieldError(
                field_name="Goods",
                messages=["At least one 'section 58(2) - obsolete' must be added"],
            )
        )
        errors.add(section_errors)

    if application.section58_other and not has_section58_other_goods:
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section582-other"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 58(2) - Other", url=url)
        section_errors.add(
            FieldError(
                field_name="Add Section 5",
                messages=["At least one section 'section 58(2) - other' must be added"],
            )
        )
        errors.add(section_errors)

    # Check "Licence For" sections match application goods lines.
    licence_for_checks = (
        (has_section1_goods, application.section1),
        (has_section2_goods, application.section2),
        (has_section5_goods, application.section5),
        (has_section58_obsolete_goods, application.section58_obsolete),
        (has_section58_other_goods, application.section58_other),
    )
    for has_goods, section in licence_for_checks:
        if has_goods and not section:
            application_details_errors.add(
                FieldError(
                    field_name="Firearm Licence For",
                    messages=[
                        "The sections selected here do not match those selected in the goods items."
                    ],
                )
            )

    # Add application detail errors now we have checked licence for
    errors.add(application_details_errors)

    importer_has_section5 = application.importer.section5_authorities.currently_active().exists()
    selected_section5 = application.verified_section5.currently_active().exists()

    # Verified Section 5
    if application.section5 and importer_has_section5 and not selected_section5:
        url = reverse("import:fa:manage-certificates", kwargs={"application_pk": application.pk})
        section_errors = PageErrors(page_name="Certificates - Section 5 Authority", url=url)
        section_errors.add(
            FieldError(
                field_name="Verified Section 5 Authorities",
                messages=[
                    "Please ensure you have selected at least one verified Section 5 Authority"
                ],
            )
        )
        errors.add(section_errors)

    # User Section 5
    if (
        application.section5
        and not importer_has_section5
        and not application.user_section5.filter(is_active=True).exists()
    ):
        url = reverse(
            "import:fa-sil:add-section5-document", kwargs={"application_pk": application.pk}
        )
        section_errors = PageErrors(page_name="Certificates - Section 5 Authority", url=url)
        section_errors.add(
            FieldError(
                field_name="Section 5 Authorities",
                messages=[
                    "Please ensure you have uploaded at least one Section 5 Authority document."
                ],
            )
        )
        errors.add(section_errors)

    # Certificates errors
    correct_section = any((application.section1, application.section2, application.section5))

    has_certificates = (
        application.user_imported_certificates.filter(is_active=True).exists()
        or application.verified_certificates.filter(is_active=True).exists()
    )

    if correct_section and not has_certificates:
        certificate_errors = PageErrors(
            page_name="Certificates",
            url=reverse("import:fa:manage-certificates", kwargs={"application_pk": application.pk}),
        )

        certificate_errors.add(
            FieldError(
                field_name="Certificate", messages=["At least one certificate must be added"]
            )
        )

        errors.add(certificate_errors)

    user_imported_certificates = application.user_imported_certificates.filter(is_active=True)

    for cert in user_imported_certificates:
        page_errors = PageErrors(
            page_name=f"Certificate - {cert.reference}",
            url=reverse(
                "import:fa:edit-certificate",
                kwargs={"application_pk": application.pk, "certificate_pk": cert.pk},
            ),
        )

        create_page_errors(
            UserImportCertificateForm(
                data=model_to_dict(cert), instance=cert, application=application
            ),
            page_errors,
        )
        errors.add(page_errors)

    errors.add(get_org_update_request_errors(application, "import"))

    return errors
