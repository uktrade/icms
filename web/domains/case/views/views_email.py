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

from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CFSProduct,
    CFSSchedule,
)
from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.sanction_email.models import SanctionEmail
from web.domains.template.models import Template
from web.flow.models import ProcessTypes, Task
from web.models import (
    DFLApplication,
    GMPFile,
    OpenIndividualLicenceApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
)
from web.notify import email
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3, get_s3_client

from .. import forms, models
from ..types import ApplicationsWithCaseEmail, CaseEmailConfig, ImpOrExp
from ..utils import get_application_current_task
from .utils import get_class_imp_or_exp

if TYPE_CHECKING:
    from django.db.models import QuerySet


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_case_emails(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

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
        "task": task,
        "page_title": "Manage Emails",
        "case_emails": application.case_emails.filter(is_active=True),
        "case_type": case_type,
        "info_email": info_email,
    }

    return render(
        request=request,
        template_name="web/domains/case/manage/case-emails.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def create_case_email(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)

    with transaction.atomic():
        imp_exp_application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )
        application: ApplicationsWithCaseEmail = _get_case_email_application(imp_exp_application)

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

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
@permission_required("web.reference_data_access", raise_exception=True)
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

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        case_email = get_object_or_404(
            application.case_emails.filter(is_active=True), pk=case_email_pk
        )

        case_email_config = _get_case_email_config(application)
        if request.POST:
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

                    email.send_email(
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
            "task": task,
            "page_title": "Edit Email",
            "form": form,
            "case_type": case_type,
        }

        return render(
            request=request,
            template_name="web/domains/case/manage/edit-case-email.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
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

        get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        case_email.is_active = False
        case_email.save()

        return redirect(
            reverse(
                "case:manage-case-emails",
                kwargs={"application_pk": application_pk, "case_type": case_type},
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
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

        task = get_application_current_task(application, case_type, Task.TaskType.PROCESS)

        case_email = get_object_or_404(application.case_emails, pk=case_email_pk)

        if request.POST:
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
            "task": task,
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
        choices = [(settings.ICMS_CFS_HSE_EMAIL, settings.ICMS_CFS_HSE_EMAIL)]
        files = File.objects.none()

        return CaseEmailConfig(application=application, to_choices=choices, file_qs=files)

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        choices = [(settings.ICMS_GMP_BEIS_EMAIL, settings.ICMS_GMP_BEIS_EMAIL)]

        app_files: "QuerySet[GMPFile]" = application.supporting_documents.filter(is_active=True)
        ft = GMPFile.Type
        ct = CertificateOfGoodManufacturingPracticeApplication.CertificateTypes

        if application.gmp_certificate_issued == ct.ISO_22716:
            files = app_files.filter(file_type__in=[ft.ISO_22716, ft.ISO_17021, ft.ISO_17065])
        elif application.gmp_certificate_issued == ct.BRC_GSOCP:
            files = app_files.filter(file_type=ft.BRC_GSOCP)
        else:
            files = File.objects.none()

        return CaseEmailConfig(application=application, to_choices=choices, file_qs=files)

    else:
        raise Exception(f"CaseEmail for application not supported {application.process_type}")


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
        raise Exception(f"CaseEmail for application not supported {application.process_type}")


def _create_email(application: ApplicationsWithCaseEmail) -> models.CaseEmail:
    # import applications
    if application.process_type in [
        OpenIndividualLicenceApplication.PROCESS_TYPE,
        DFLApplication.PROCESS_TYPE,
        SILApplication.PROCESS_TYPE,
    ]:
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
        cc_address_list = [settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL]

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
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
        cc_address_list = []

    # certificate applications
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        template = Template.objects.get(is_active=True, template_code="CA_HSE_EMAIL")
        content = template.get_content(
            {
                "CASE_REFERENCE": application.reference,
                "APPLICATION_TYPE": ProcessTypes.CFS.label,  # type: ignore[attr-defined]
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
        cc_address_list = []

    elif application.process_type == CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE:
        template = Template.objects.get(is_active=True, template_code="CA_BEIS_EMAIL")
        content = template.get_content(
            {
                "CASE_REFERENCE": application.reference,
                "APPLICATION_TYPE": ProcessTypes.GMP.label,  # type: ignore[attr-defined]
                "EXPORTER_NAME": application.exporter,
                "EXPORTER_ADDRESS": application.exporter_office,
                "MANUFACTURER_NAME": application.manufacturer_name,
                "MANUFACTURER_ADDRESS": application.manufacturer_address,
                "MANUFACTURER_POSTCODE": application.manufacturer_postcode,
                "RESPONSIBLE_PERSON_NAME": application.responsible_person_name,
                "RESPONSIBLE_PERSON_ADDRESS": application.responsible_person_address,
                "RESPONSIBLE_PERSON_POSTCODE": application.responsible_person_postcode,
                "BRAND_NAMES": ", ".join([b.brand_name for b in application.brands.all()]),
                "CASE_OFFICER_NAME": application.case_owner.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )
        cc_address_list = []

    else:
        raise Exception(f"CaseEmail for application not supported {application.process_type}")

    return models.CaseEmail.objects.create(
        status=models.CaseEmail.Status.DRAFT,
        subject=template.template_title,
        body=content,
        cc_address_list=cc_address_list,
    )
