from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import BooleanField, ExpressionWrapper, Q, Window
from django.db.models.functions import RowNumber
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.case import forms, models
from web.domains.case.services import case_progress
from web.domains.case.types import ApplicationsWithCaseEmail, CaseEmailConfig, ImpOrExp
from web.domains.case.utils import case_documents_metadata
from web.flow.models import ProcessTypes
from web.mail.constants import CaseEmailCodes
from web.mail.emails import create_case_email, send_case_email
from web.models import (
    CaseEmail,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    Constabulary,
    DFLApplication,
    File,
    GMPFile,
    OpenIndividualLicenceApplication,
    SanctionEmail,
    SanctionsAndAdhocApplication,
    SILApplication,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest

from .utils import get_caseworker_view_readonly_status, get_class_imp_or_exp

if TYPE_CHECKING:
    from django.db.models import QuerySet


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_case_emails(
    request: AuthenticatedHttpRequest, *, application_pk: int, case_type: str
) -> HttpResponse:
    model_class = get_class_imp_or_exp(case_type)
    with transaction.atomic():
        application: ImpOrExp = get_object_or_404(
            model_class.objects.select_for_update(), pk=application_pk
        )

        readonly_view = get_caseworker_view_readonly_status(application, case_type, request.user)

    email_title = "Emails"
    email_subtitle = ""
    no_emails_msg = "There aren't any emails."
    # Used in template to change how case email attachments get displayed.
    is_firearms_application = False

    if application.process_type in [ProcessTypes.FA_OIL, ProcessTypes.FA_DFL, ProcessTypes.FA_SIL]:
        info_email = (
            "This screen is used to email relevant constabularies. You may attach multiple"
            " firearms certificates to a single email. You can also record responses from the constabulary."
        )
        is_firearms_application = True

    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        email_title = "Health and Safety Executive (HSE) Checks"
        email_subtitle = "HSE Emails"
        info_email = "Biocidal products: this screen is used to email and record responses from the Health and Safety Executive."
        no_emails_msg = "There aren't any HSE emails."

    else:
        info_email = ""

    verified_section_5_authorities = []
    verified_firearms_authorities = []

    if application.process_type in [
        SILApplication.PROCESS_TYPE,
        OpenIndividualLicenceApplication.PROCESS_TYPE,
    ]:
        # it's a SIL or OIL application, get the verified firearm authorities
        today_date = timezone.now().date()
        specific_application = application.get_specific_model()
        verified_firearms_authorities = specific_application.verified_certificates.all().annotate(
            is_expired=ExpressionWrapper(Q(end_date__lt=today_date), output_field=BooleanField())
        )

        if application.process_type == SILApplication.PROCESS_TYPE:
            verified_section_5_authorities = specific_application.verified_section5.all().annotate(
                is_expired=ExpressionWrapper(
                    Q(end_date__lt=today_date), output_field=BooleanField()
                )
            )

    case_emails = (
        application.case_emails.filter(is_active=True)
        # Show most recent first
        .order_by("-pk")
        # Count the emails oldest to newest
        .annotate(email_num=Window(expression=RowNumber(), order_by="pk"))
    )

    file_metadata = case_documents_metadata(application.get_specific_model())

    context = {
        "process": application,
        "page_title": "Manage Emails",
        "case_emails": case_emails,
        "is_firearms_application": is_firearms_application,
        "file_metadata": file_metadata,
        "case_type": case_type,
        "email_title": email_title,
        "email_subtitle": email_subtitle,
        "no_emails_msg": no_emails_msg,
        "info_email": info_email,
        "readonly_view": readonly_view,
        "record_response_form": forms.CaseEmailResponseForm(),
        "verified_section_5_authorities": verified_section_5_authorities,
        "verified_firearms_authorities": verified_firearms_authorities,
    }

    return render(
        request=request,
        template_name="web/domains/case/manage/case-emails.html",
        context=context,
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
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
                    send_case_email(case_email, request.user)

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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
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

        case_email = get_object_or_404(
            application.case_emails,
            pk=case_email_pk,
            # Prevent draft emails being closed.
            status__in=[CaseEmail.Status.OPEN, CaseEmail.Status.CLOSED],
        )

        if request.method == "POST":
            form = forms.CaseEmailResponseForm(request.POST, instance=case_email)
            if form.is_valid():
                case_email = form.save(commit=False)
                case_email.status = models.CaseEmail.Status.CLOSED
                case_email.closed_datetime = timezone.now()
                case_email.closed_by = request.user
                case_email.save()

                return redirect(
                    reverse(
                        "case:manage-case-emails",
                        kwargs={"application_pk": application_pk, "case_type": case_type},
                    )
                )
        else:
            form = forms.CaseEmailResponseForm(instance=case_email)

        file_metadata = case_documents_metadata(application.get_specific_model())
        is_firearms_application = application.process_type in [
            ProcessTypes.FA_OIL,
            ProcessTypes.FA_DFL,
            ProcessTypes.FA_SIL,
        ]

        context = {
            "process": application,
            "is_firearms_application": is_firearms_application,
            "file_metadata": file_metadata,
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
            # Verified Firearms Authority
            Q(firearmsauthority__oil_application=application)
            | Q(userimportcertificate__oil_application=application),
            is_active=True,
        )

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_metadata=case_documents_metadata(application),
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
            file_metadata=case_documents_metadata(application),
            file_qs=files,
        )

    elif application.process_type == SILApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in Constabulary.objects.filter(is_active=True)
        ]
        files = File.objects.filter(
            # Verified Firearms Authority
            Q(firearmsauthority__sil_application=application)
            | Q(userimportcertificate__sil_application=application)
            # Section 5 Authority
            | Q(section5authority__sil_application=application)
            | Q(silusersection5__sil_application=application),
            is_active=True,
        )

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_metadata=case_documents_metadata(application),
            file_qs=files,
        )

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        choices = [
            (c.email, f"{c.name} ({c.email})") for c in SanctionEmail.objects.filter(is_active=True)
        ]
        files = application.supporting_documents.filter(is_active=True)

        return CaseEmailConfig(
            application=application,
            to_choices=choices,
            file_metadata=case_documents_metadata(application),
            file_qs=files,
        )

    # certificate application
    elif application.process_type == CertificateOfFreeSaleApplication.PROCESS_TYPE:
        files = File.objects.none()
        file_metadata = case_documents_metadata(application)

        return CaseEmailConfig(application=application, file_qs=files, file_metadata=file_metadata)

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

        return CaseEmailConfig(
            application=application,
            file_qs=files,
            file_metadata=case_documents_metadata(application),
        )

    else:
        raise ValueError(f"CaseEmail for application not supported {application.process_type}")


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
            return create_case_email(
                application,
                CaseEmailCodes.CONSTABULARY_CASE_EMAIL,
                cc=[settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL],
            )

        case pt.SANCTIONS:
            return create_case_email(application, CaseEmailCodes.SANCTIONS_CASE_EMAIL)

        # certificate applications
        case pt.CFS:
            return create_case_email(
                application, CaseEmailCodes.HSE_CASE_EMAIL, settings.ICMS_CFS_HSE_EMAIL
            )

        case pt.GMP:
            attachments = application.supporting_documents.filter(is_active=True)
            return create_case_email(
                application,
                CaseEmailCodes.BEIS_CASE_EMAIL,
                settings.ICMS_GMP_BEIS_EMAIL,
                attachments=attachments,
            )

        case _:
            raise ValueError(f"CaseEmail for application not supported {application.process_type}")
