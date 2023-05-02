from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.case._import.fa.types import FaImportApplication
from web.domains.case.services import case_progress
from web.flow.models import ProcessTypes
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CFSProduct,
    CFSSchedule,
    Constabulary,
    DFLApplication,
    File,
    GMPFile,
    OpenIndividualLicenceApplication,
    SanctionEmail,
    SanctionsAndAdhocApplication,
    SILApplication,
    Template,
)
from web.notify.email import send_email
from web.notify.utils import create_case_email
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3, get_s3_client

from .. import forms, models
from ..types import ApplicationsWithCaseEmail, CaseEmailConfig, ImpOrExp
from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp

if TYPE_CHECKING:
    from django.db.models import QuerySet


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_case_emails(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

    if application.process_type in [
        OpenIndividualLicenceApplication.PROCESS_TYPE,
        DFLApplication.PROCESS_TYPE,
        SILApplication.PROCESS_TYPE,
    ]:
        info_email = (
            "This screen is used to email relevant constabularies. You may attach multiple"
            " firearms certificates to a single email. You can also record responses from the constabulary."
        )
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        info_email = "Biocidal products: this screen is used to email and record responses from the Health and Safety Executive."

    else:
        info_email = ""

    context = {
        "process": application,
        "page_title": "Manage Emails",
        "case_emails": application.case_emails.filter(is_active=True),
        "case_type": case_type,
        "info_email": info_email,
        "readonly_view": readonly_view,
    }

    return render(
        request=request,
        template_name="web/domains/case/manage/case-emails.html",
        context=context,
    )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def create_draft_case_email(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        imp_exp_application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        application: ApplicationsWithCaseEmail = _get_case_email_application(imp_exp_application)

        case_progress.application_in_processing(application)

        email: models.CaseEmail = _create_email(application)
        application.case_emails.add(email)

        return redirect(
            reverse(
                "case:edit-case-email",
                kwargs={
                    "application_pk": application.pk,
                    "case_email_pk": email.pk,
                    "case_type": case_type,
                },
            )
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_case_email(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_email_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        imp_exp_application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        application: ApplicationsWithCaseEmail = _get_case_email_application(imp_exp_application)

        case_progress.application_in_processing(application)

        case_email = get_object_or_404(
            application.case_emails.filter(is_active=True), pk=case_email_pk
        )

        case_email_config = _get_case_email_config(application)
        if request.method == "POST":
            form = forms.CaseEmailForm(
                request.POST, instance=case_email, case_email_config=case_email_config
            )
            if form.is_valid():
                case_email = form.save()

                if "send" in request.POST:
                    attachments = []
                    s3_client = get_s3_client()

                    for document in case_email.attachments.all():
                        file_content = get_file_from_s3(document.path, client=s3_client)
                        attachments.append((document.filename, file_content))

                    send_email(
                        case_email.subject,
                        case_email.body,
                        [case_email.to],
                        case_email.cc_address_list,
                        attachments,
                    )

                    case_email.status = models.CaseEmail.Status.OPEN
                    case_email.sent_datetime = timezone.now()
                    case_email.save()

                    return redirect(
                        reverse(
                            "case:manage-case-emails",
                            kwargs={"application_pk": application_pk, "case_type": case_type},
                        )
                    )

                return redirect(
                    reverse(
                        "case:edit-case-email",
                        kwargs={
                            "application_pk": application_pk,
                            "case_email_pk": case_email_pk,
                            "case_type": case_type,
                        },
                    )
                )
        else:
            form = forms.CaseEmailForm(instance=case_email, case_email_config=case_email_config)

        context = {
            "process": application,
            "page_title": "Edit Email",
            "form": form,
            "case_type": case_type,
            "case_email": case_email,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/edit-case-email.html",
            context=context,
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def archive_case_email(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_email_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        case_email = get_object_or_404(
            application.case_emails.filter(is_active=True), pk=case_email_pk
        )

        case_progress.application_in_processing(application)

        case_email.is_active = False
        case_email.save()

        return redirect(
            reverse(
                "case:manage-case-emails",
                kwargs={"application_pk": application_pk, "case_type": case_type},
            )
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def add_response_case_email(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    case_email_pk: int,
    case_type: str,
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        case_email = get_object_or_404(application.case_emails, pk=case_email_pk)

        if request.method == "POST":
            form = forms.CaseEmailResponseForm(request.POST, instance=case_email)
            if form.is_valid():
                case_email = form.save(commit=False)
                case_email.status = models.CaseEmail.Status.CLOSED
                case_email.closed_datetime = timezone.now()
                case_email.save()

                return redirect(
                    reverse(
                        "case:manage-case-emails",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = forms.CaseEmailResponseForm(instance=case_email)

        context = {
            "process": application,
            "page_title": "Add Response for Email",
            "form": form,
            "object": case_email,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/add-response-case-email.html",
            context=context,
        )


def _get_case_email_config(application: ApplicationsWithCaseEmail) -> CaseEmailConfig:
    # import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = File.objects.filter(
            Q(firearmsauthority__oil_application=application)
            | Q(userimportcertificate__oil_application=application)
        )

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_qs=files,
        )

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = application.goods_certificates.filter(is_active=True)

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_qs=files,
        )

    elif application.process_type == SILApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = File.objects.filter(
            Q(firearmsauthority__sil_application=application)
            | Q(userimportcertificate__sil_application=application)
            | Q(silusersection5__sil_application=application)
        )

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_qs=files,
        )

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in SanctionEmail.objects.filter(is_active=True)
        ]
        files = application.supporting_documents.filter(is_active=True)

        return CaseEmailConfig(application=application, to_choices=choices, file_qs=files)

    # certificate application
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        files = File.objects.none()

        return CaseEmailConfig(application=application, file_qs=files)

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        app_files: "QuerySet[GMPFile]" = application.supporting_documents.filter(is_active=True)
        ft = GMPFile.Type
        ct = CertificateOfGoodManufacturingPracticeApplication.CertificateTypes

        if application.gmp_certificate_issued == ct.ISO_22716:
            files = app_files.filter(file_type__in=[ft.ISO_22716, ft.ISO_17021, ft.ISO_17065])
        elif application.gmp_certificate_issued == ct.BRC_GSOCP:
            files = app_files.filter(file_type=ft.BRC_GSOCP)
        else:
            files = File.objects.none()

        return CaseEmailConfig(application=application, file_qs=files)

    else:
        raise ValueError(f"CaseEmail for application not supported {application.process_type}")


def _get_selected_product_data(biocidal_schedules: "QuerySet[CFSSchedule]") -> str:
    products = CFSProduct.objects.filter(schedule__in=biocidal_schedules)
    product_data = []

    for p in products:
        p_types = (str(pk) for pk in p.product_type_numbers.values_list("pk", flat=True))
        ingredient_list = p.active_ingredients.values_list("name", "cas_number")
        ingredients = (f"{name} ({cas})" for name, cas in ingredient_list)

        product = "\n".join(
            [
                f"Product: {p.product_name}",
                f"Product type numbers: {', '.join(p_types)}",
                f"Active ingredients (CAS numbers): f{', '.join(ingredients)}",
            ]
        )
        product_data.append(product)

    return "\n\n".join(product_data)


def _get_case_email_application(application: ImpOrExp) -> ApplicationsWithCaseEmail:
    # import applications
    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return application.openindividuallicenceapplication

    elif application.process_type == DFLApplication.PROCESS_TYPE:
        return application.dflapplication

    elif application.process_type == SILApplication.PROCESS_TYPE:
        return application.silapplication

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return application.sanctionsandadhocapplication

    # certificate application
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        return application.certificateoffreesaleapplication

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        return application.certificateofgoodmanufacturingpracticeapplication

    else:
        raise ValueError(f"CaseEmail for application not supported {application.process_type}")


def _create_email(application: ApplicationsWithCaseEmail) -> models.CaseEmail:
    pt = ProcessTypes

    match application.process_type:
        # import applications
        case pt.FA_OIL | pt.FA_DFL | pt.FA_SIL:
            return _create_fa_case_email(application)

        case pt.SANCTIONS:
            return _create_sanction_case_email(application)

        # certificate applications
        case pt.CFS:
            return create_cfs_case_email(application)

        case pt.GMP:
            attachments = application.supporting_documents.filter(is_active=True)
            return create_case_email(
                application, "CA_BEIS_EMAIL", settings.ICMS_GMP_BEIS_EMAIL, attachments=attachments
            )

        case _:
            raise ValueError(f"CaseEmail for application not supported {application.process_type}")


def _create_fa_case_email(application: FaImportApplication) -> models.CaseEmail:
    template = Template.objects.get(is_active=True, template_code="IMA_CONSTAB_EMAIL")
    goods_description = (
        "Firearms, component parts thereof, or ammunition of any applicable"
        " commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended."
    )
    content = template.get_content(
        {
            "CASE_REFERENCE": application.reference,
            "IMPORTER_NAME": application.importer.display_name,
            "IMPORTER_ADDRESS": application.importer_office,
            "GOODS_DESCRIPTION": goods_description,
            "CASE_OFFICER_NAME": application.case_owner.full_name,
            "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
            "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
        }
    )
    return models.CaseEmail.objects.create(
        subject=template.template_title,
        body=content,
        cc_address_list=[settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL],
    )


def _create_sanction_case_email(application: SanctionsAndAdhocApplication) -> models.CaseEmail:
    template = Template.objects.get(is_active=True, template_code="IMA_SANCTION_EMAIL")
    goods_descriptions = application.sanctionsandadhocapplicationgoods_set.values_list(
        "goods_description", flat=True
    )
    content = template.get_content(
        {
            "CASE_REFERENCE": application.reference,
            "IMPORTER_NAME": application.importer.display_name,
            "IMPORTER_ADDRESS": application.importer_office,
            "GOODS_DESCRIPTION": "\n".join(goods_descriptions),
            "CASE_OFFICER_NAME": application.case_owner.full_name,
            "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
            "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
        }
    )

    return models.CaseEmail.objects.create(
        subject=template.template_title,
        body=content,
    )


def create_cfs_case_email(application: CertificateOfFreeSaleApplication) -> models.CaseEmail:
    template = Template.objects.get(is_active=True, template_code="CA_HSE_EMAIL")
    content = template.get_content(
        {
            "CASE_REFERENCE": application.reference,
            "APPLICATION_TYPE": ProcessTypes.CFS.label,
            "EXPORTER_NAME": application.exporter,
            "EXPORTER_ADDRESS": application.exporter_office,
            "CONTACT_EMAIL": application.contact.email,
            "CERT_COUNTRIES": "\n".join(
                application.countries.filter(is_active=True).values_list("name", flat=True)
            ),
            "SELECTED_PRODUCTS": _get_selected_product_data(
                application.schedules.filter(legislations__is_biocidal=True)
            ),
            "CASE_OFFICER_NAME": application.case_owner.full_name,
            "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
            "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
        }
    )
    return models.CaseEmail.objects.create(
        to=settings.ICMS_CFS_HSE_EMAIL,
        subject=template.template_title,
        body=content,
    )
