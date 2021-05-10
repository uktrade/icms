from typing import Any, Dict, Type, Union

import weasyprint
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import get_users_with_perms

from web.domains.case.forms import CloseCaseForm
from web.domains.firearms.models import FirearmsAuthority
from web.domains.importer.models import Importer
from web.domains.template.models import Template
from web.flow.models import Task
from web.notify.email import send_email
from web.utils.s3 import get_file_from_s3

from .. import views as case_views
from . import forms
from .derogations.models import DerogationsApplication
from .fa_dfl.models import DFLApplication
from .fa_oil.models import OpenIndividualLicenceApplication
from .fa_sil.models import SILApplication
from .forms import ImportContactLegalEntityForm, ImportContactPersonForm
from .models import (
    ImportApplication,
    ImportApplicationType,
    ImportContact,
    WithdrawImportApplication,
)
from .sanctions.models import SanctionsAndAdhocApplication
from .wood.models import WoodQuotaApplication


class ImportApplicationChoiceView(TemplateView, PermissionRequiredMixin):
    template_name = "web/domains/case/import/choice.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_derogations(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.DEROGATION
    model_class = DerogationsApplication
    redirect_view = "import:derogations:edit-derogations"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sanctions(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.SANCTION_ADHOC
    model_class = SanctionsAndAdhocApplication
    redirect_view = "import:sanctions:edit-application"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_oil(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.OIL
    model_class = OpenIndividualLicenceApplication
    redirect_view = "import:fa-oil:edit-oil"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_dfl(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.DFL
    model_class = DFLApplication
    redirect_view = "import:fa-dfl:edit"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_firearms_sil(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.SubTypes.SIL
    model_class = SILApplication
    redirect_view = "import:fa-sil:edit"
    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_wood_quota(request: HttpRequest) -> HttpResponse:
    import_application_type = ImportApplicationType.Types.WOOD_QUOTA
    model_class = WoodQuotaApplication
    redirect_view = "import:wood:edit-quota"

    return _create_application(
        request,
        import_application_type,  # type: ignore[arg-type]
        model_class,
        redirect_view,
        form_class=forms.CreateWoodQuotaApplicationForm,
    )


def _create_application(
    request: HttpRequest,
    import_application_type: Union[ImportApplicationType.Types, ImportApplicationType.SubTypes],
    model_class: Type[ImportApplication],
    redirect_view: str,
    form_class: Type[forms.CreateImportApplicationForm] = None,
) -> HttpResponse:
    """Helper function to create one of several types of importer application.

    :param request: Django request
    :param import_application_type: ImportApplicationType type or sub_type
    :param model_class: ImportApplication class
    :param redirect_view: View to redirect to
    :param form_class: Optional form class that defines extra logic
    :return:
    """

    application_type: ImportApplicationType = ImportApplicationType.objects.get(
        Q(type=import_application_type) | Q(sub_type=import_application_type)
    )

    if form_class is None:
        form_class = forms.CreateImportApplicationForm

    if request.POST:
        form = form_class(request.POST, user=request.user)

        if form.is_valid():
            application = model_class()
            application.importer = form.cleaned_data["importer"]
            application.importer_office = form.cleaned_data["importer_office"]
            application.process_type = model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = application_type

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)

            return redirect(reverse(redirect_view, kwargs={"pk": application.pk}))
    else:
        form = form_class(user=request.user)

    context = {"form": form, "import_application_type": application_type}

    return render(request, "web/domains/case/import/create.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def take_ownership(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=pk
        )
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")
        application.case_owner = request.user
        # Licence start date is set when ILB Admin takes the case
        application.licence_start_date = timezone.now().date()
        application.save()

        return redirect(reverse("import:case-management", kwargs={"pk": application.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def release_ownership(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        application.get_task(ImportApplication.SUBMITTED, "process")
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")
        application.case_owner = None
        application.save()

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_case(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = CloseCaseForm(request.POST)
            if form.is_valid():
                application.status = ImportApplication.STOPPED
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                if form.cleaned_data.get("send_email"):
                    template = Template.objects.get(template_code="STOP_CASE")

                    subject = template.get_title({"CASE_REFERENCE": application.pk})
                    body = template.get_content({"CASE_REFERENCE": application.pk})
                    users = get_users_with_perms(
                        application.importer, only_with_perms_in=["is_contact_of_importer"]
                    ).filter(user_permissions__codename="importer_access")
                    recipients = set(users.values_list("email", flat=True))

                    send_email(subject, body, recipients)

                return redirect(reverse("workbasket"))
        else:
            form = CloseCaseForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Management",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/case.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_withdrawals(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )
        withdrawals = application.withdrawals.filter(is_active=True)
        current_withdrawal = withdrawals.filter(
            status=WithdrawImportApplication.STATUS_OPEN
        ).first()

        if request.POST:
            form = forms.WithdrawResponseForm(request.POST, instance=current_withdrawal)
            if form.is_valid():
                withdrawal = form.save(commit=False)
                withdrawal.response_by = request.user
                withdrawal.save()

                # withdrawal accepted - case is closed
                # else case still open
                if withdrawal.status == WithdrawImportApplication.STATUS_ACCEPTED:
                    application.is_active = False
                    application.save()

                    task.is_active = False
                    task.finished = timezone.now()
                    task.save()

                    return redirect(reverse("workbasket"))
                else:
                    application.status = ImportApplication.SUBMITTED
                    application.save()

                    task.is_active = False
                    task.finished = timezone.now()
                    task.save()

                    Task.objects.create(process=application, task_type="process", previous=task)

                    return redirect(reverse("import:manage-withdrawals", kwargs={"pk": pk}))
        else:
            form = forms.WithdrawResponseForm(instance=current_withdrawal)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Withdrawals",
            "form": form,
            "withdrawals": withdrawals,
            "current_withdrawal": current_withdrawal,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/withdrawals.html",
            context=context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def withdraw_case(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = forms.WithdrawForm(request.POST)
            if form.is_valid():
                withdrawal = form.save(commit=False)
                withdrawal.import_application = application
                withdrawal.request_by = request.user
                withdrawal.save()

                application.status = ImportApplication.WITHDRAWN
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(process=application, task_type="process", previous=task)

                return redirect(reverse("workbasket"))
        else:
            form = forms.WithdrawForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Management",
            "form": form,
            "withdrawals": application.withdrawals.filter(is_active=True),
        }
        return render(request, "web/domains/case/import/withdraw.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def archive_withdrawal(request, application_pk, withdrawal_pk):
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        withdrawal = get_object_or_404(application.withdrawals, pk=withdrawal_pk)

        task = application.get_task(ImportApplication.WITHDRAWN, "process")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        application.status = ImportApplication.SUBMITTED
        application.save()

        withdrawal.is_active = False
        withdrawal.save()

        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(process=application, task_type="process", previous=task)

        return redirect(reverse("workbasket"))


@login_required
def view_case(request: HttpRequest, pk: int) -> HttpResponse:
    has_perm_importer = request.user.has_perm("web.importer_access")
    has_perm_reference_data = request.user.has_perm("web.reference_data_access")

    if not has_perm_importer and not has_perm_reference_data:
        raise PermissionDenied

    application: ImportApplication = get_object_or_404(ImportApplication, pk=pk)

    # first check is for case managers (who are not marked as contacts of
    # importers), second is for people submitting applications
    if not has_perm_reference_data and not request.user.has_perm(
        "web.is_contact_of_importer", application.importer
    ):
        raise PermissionDenied

    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return _view_firearms_oil_case(request, application.openindividuallicenceapplication)

    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return _view_sanctions_and_adhoc_case(request, application.sanctionsandadhocapplication)

    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        return _view_wood_quota_application(request, application.woodquotaapplication)

    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        return _view_derogations(request, application.derogationsapplication)

    else:
        return _view_case(request, application)


def _view_firearms_oil_case(
    request: HttpRequest, application: OpenIndividualLicenceApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "verified_certificates": FirearmsAuthority.objects.filter(
            verified_certificates__in=application.verified_certificates.all()
        ),
        "certificates": application.user_imported_certificates.active(),
        "contacts": application.importcontact_set.all(),
    }
    return render(request, "web/domains/case/import/view_firearms_oil_case.html", context)


def _view_sanctions_and_adhoc_case(
    request: HttpRequest, application: SanctionsAndAdhocApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "goods": application.sanctionsandadhocapplicationgoods_set.all(),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }
    return render(request, "web/domains/case/import/view_sanctions_and_adhoc_case.html", context)


def _view_wood_quota_application(
    request: HttpRequest, application: WoodQuotaApplication
) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "contract_documents": application.contract_documents.filter(is_active=True),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }

    return render(request, "web/domains/case/import/wood/view.html", context)


def _view_derogations(request: HttpRequest, application: DerogationsApplication) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
        "supporting_documents": application.supporting_documents.filter(is_active=True),
    }
    return render(request, "web/domains/case/import/view_derogations.html", context)


def _view_case(request: HttpRequest, application: ImportApplication) -> HttpResponse:
    context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "process": application,
        "page_title": application.application_type.get_type_description(),
    }
    return render(request, "web/domains/case/import/view_case.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def list_notes(request, pk):
    process_template = "web/domains/case/import/partials/process.html"
    base_template = "flow/task-manage-import.html"
    return case_views._list_notes(
        request, pk, ImportApplication, "import", process_template, base_template
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def add_note(request, pk):
    return case_views._add_note(request, pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_note(request, application_pk, note_pk):
    return case_views._archive_note(request, application_pk, note_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def unarchive_note(request, application_pk, note_pk):
    return case_views._unarchive_note(request, application_pk, note_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_note(request: HttpRequest, application_pk: int, note_pk: int) -> HttpResponse:
    process_template = "web/domains/case/import/partials/process.html"
    base_template = "flow/task-manage-import.html"

    return case_views._edit_note(
        request,
        application_pk,
        note_pk,
        ImportApplication,
        "import",
        process_template,
        base_template,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_note_document(request: HttpRequest, application_pk: int, note_pk: int) -> HttpResponse:
    process_template = "web/domains/case/import/partials/process.html"
    base_template = "flow/task-manage-import.html"

    return case_views._add_note_document(
        request,
        application_pk,
        note_pk,
        ImportApplication,
        "import",
        process_template,
        base_template,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_GET
def view_note_document(
    request: HttpRequest, application_pk: int, note_pk: int, file_pk: int
) -> HttpResponse:

    return case_views.view_note_document(
        request, application_pk, note_pk, file_pk, ImportApplication
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def delete_note_document(
    request: HttpRequest, application_pk: int, note_pk: int, file_pk: int
) -> HttpResponse:

    return case_views.delete_note_document(
        request, application_pk, note_pk, file_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_update_requests(request, pk):
    application = get_object_or_404(ImportApplication, pk=pk)
    template = Template.objects.get(template_code="IMA_APP_UPDATE", is_active=True)

    importer = Importer.objects.get(import_applications__pk=pk)

    # TODO: replace with case reference
    placeholder_content = {
        "CASE_REFERENCE": pk,
        "IMPORTER_NAME": importer.display_name,
        "CASE_OFFICER_NAME": request.user,
    }

    # TODO: replace with case reference
    email_subject = template.get_title({"CASE_REFERENCE": pk})
    email_content = template.get_content(placeholder_content)

    importer_contacts = get_users_with_perms(
        application.importer, only_with_perms_in=["is_contact_of_importer"]
    ).filter(user_permissions__codename="importer_access")

    return case_views._manage_update_requests(
        request,
        application,
        ImportApplication,
        email_subject,
        email_content,
        importer_contacts,
        "import",
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def close_update_requests(request, application_pk, update_request_pk):
    return case_views._close_update_requests(
        request, application_pk, update_request_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def list_update_requests(request, pk):
    # TODO Remove mypy ignore when doing ICMSLST-648
    return case_views._list_update_requests(request, pk, ImportApplication, "import")  # type: ignore[attr-defined]


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def start_update_request(request, application_pk, update_request_pk):
    # TODO Remove mypy ignore when doing ICMSLST-648
    return case_views._start_update_request(  # type: ignore[attr-defined]
        request, application_pk, update_request_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def respond_update_request(request, application_pk, update_request_pk):
    # TODO: make url more generic
    # TODO Remove mypy ignore when doing ICMSLST-648
    return case_views._respond_update_request(  # type: ignore[attr-defined]
        request, application_pk, update_request_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_firs(request, application_pk):
    extra_context = {
        "show_firs": True,
        "process_template": "web/domains/case/import/partials/process.html",
        "base_template": "flow/task-manage-import.html",
    }
    return case_views._manage_firs(
        request, application_pk, ImportApplication, "import", **extra_context
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def add_fir(request, application_pk):
    return case_views._add_fir(request, application_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_fir(request, application_pk, fir_pk):
    application = get_object_or_404(ImportApplication, pk=application_pk)
    importer_contacts = get_users_with_perms(
        application.importer, only_with_perms_in=["is_contact_of_importer"]
    ).filter(user_permissions__codename="importer_access")

    extra_context = {
        "process_template": "web/domains/case/import/partials/process.html",
        "base_template": "flow/task-manage-import.html",
    }
    return case_views._edit_fir(
        request,
        application_pk,
        fir_pk,
        ImportApplication,
        "import",
        importer_contacts,
        **extra_context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_fir(request, application_pk, fir_pk):
    return case_views._archive_fir(request, application_pk, fir_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def withdraw_fir(request, application_pk, fir_pk):
    return case_views._withdraw_fir(request, application_pk, fir_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def close_fir(request, application_pk, fir_pk):
    return case_views._close_fir(request, application_pk, fir_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_fir_file(request, application_pk, fir_pk, file_pk):
    return case_views._archive_fir_file(
        request, application_pk, fir_pk, file_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def list_firs(request, application_pk):
    return case_views._list_firs(request, application_pk, ImportApplication, "import")


@login_required
@permission_required("web.importer_access", raise_exception=True)
def respond_fir(request, application_pk, fir_pk):
    return case_views._respond_fir(request, application_pk, fir_pk, ImportApplication, "import")


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def prepare_response(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.ResponsePreparationForm(request.POST, instance=application)
            if form.is_valid():
                form.save()
                return redirect(reverse("import:prepare-response", kwargs={"pk": pk}))
        else:
            form = forms.ResponsePreparationForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "task": task,
            "page_title": "Response Preparation",
            "form": form,
            "cover_letter_flag": application.application_type.cover_letter_flag,
        }

    if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
        return _prepare_response_oil(request, application.openindividuallicenceapplication, context)
    elif application.process_type == SanctionsAndAdhocApplication.PROCESS_TYPE:
        return _prepare_sanctions_and_adhoc_response(
            request, application.sanctionsandadhocapplication, context
        )
    elif application.process_type == DerogationsApplication.PROCESS_TYPE:
        return _prepare_derogations_response(request, application.derogationsapplication, context)
    elif application.process_type == WoodQuotaApplication.PROCESS_TYPE:
        return _prepare_wood_quota_response(request, application.woodquotaapplication, context)
    else:
        raise NotImplementedError


def _prepare_response_oil(
    request: HttpRequest, application: OpenIndividualLicenceApplication, context: Dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-firearms-oil-response.html",
        context=context,
    )


def _prepare_sanctions_and_adhoc_response(
    request: HttpRequest, application: SanctionsAndAdhocApplication, context: Dict[str, Any]
) -> HttpResponse:
    context.update(
        {"process": application, "goods": application.sanctionsandadhocapplicationgoods_set.all()}
    )

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-sanctions-response.html",
        context=context,
    )


def _prepare_derogations_response(
    request: HttpRequest, application: DerogationsApplication, context: Dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-derogations-response.html",
        context=context,
    )


def _prepare_wood_quota_response(
    request: HttpRequest, application: WoodQuotaApplication, context: Dict[str, Any]
) -> HttpResponse:
    context.update({"process": application})

    return render(
        request=request,
        template_name="web/domains/case/import/manage/prepare-wood-quota-response.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_cover_letter(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.CoverLetterForm(request.POST, instance=application)
            if form.is_valid():
                form.save()
                return redirect(reverse("import:prepare-response", kwargs={"pk": pk}))
        else:
            form = forms.CoverLetterForm(instance=application)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Cover Letter Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-cover-letter.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_licence(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.LicenceDateForm(request.POST, instance=application)
            if form.is_valid():
                form.save()
                return redirect(reverse("import:prepare-response", kwargs={"pk": pk}))
        else:
            form = forms.LicenceDateForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Licence Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-licence.html",
            context=context,
        )


def _add_endorsement(request, pk, Form):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = Form(request.POST)
            if form.is_valid():
                endorsement = form.save(commit=False)
                endorsement.import_application = application
                endorsement.save()
                return redirect(reverse("import:prepare-response", kwargs={"pk": pk}))
        else:
            form = Form()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/add-endorsement.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_endorsement(request, pk):
    return _add_endorsement(request, pk, forms.EndorsementChoiceImportApplicationForm)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_custom_endorsement(request, pk):
    return _add_endorsement(request, pk, forms.EndorsementImportApplicationForm)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_endorsement(request, application_pk, endorsement_pk):
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        if request.POST:
            form = forms.EndorsementImportApplicationForm(request.POST, instance=endorsement)
            if form.is_valid():
                form.save()
                return redirect(reverse("import:prepare-response", kwargs={"pk": application_pk}))
        else:
            form = forms.EndorsementImportApplicationForm(instance=endorsement)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Endorsement Response Preparation",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/edit-endorsement.html",
            context=context,
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def delete_endorsement(request, application_pk, endorsement_pk):
    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        endorsement = get_object_or_404(application.endorsements, pk=endorsement_pk)
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        endorsement.delete()

        return redirect(reverse("import:prepare-response", kwargs={"pk": application_pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def preview_cover_letter(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        context = {
            "process": application,
            "task": task,
            "page_title": "Cover Letter Preview",
            "issue_date": application.licence_issue_date.strftime("%d %B %Y"),
            "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
        }

        html_string = render_to_string(
            request=request,
            template_name="web/domains/case/import/manage/preview-cover-letter.html",
            context=context,
        )

        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = "filename=CoverLetter.pdf"
        return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def preview_licence(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        context = {
            "process": application,
            "task": task,
            "page_title": "Licence Preview",
            "issue_date": application.licence_issue_date.strftime("%d %B %Y"),
        }

        html_string = render_to_string(
            request=request,
            template_name="web/domains/case/import/manage/preview-licence.html",
            context=context,
        )

        html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = "filename=Licence.pdf"
        return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def authorisation(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )

        application_errors = []
        if application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
            if not application.openindividuallicenceapplication.checklists.exists():
                url = reverse("import:fa-oil:manage-checklist", args=[application.pk])
                html = f"<a href='{url}'>Please complete checklist.</a>"
                application_errors.append(html)

        if application.decision == ImportApplication.REFUSE:
            url = reverse("import:prepare-response", args=[application.pk])
            html = f"<a href='{url}'>Please approve application.</a>"
            application_errors.append(html)

        if not application.licence_start_date or not application.licence_end_date:
            url = reverse("import:prepare-response", args=[application.pk])
            html = f"<a href='{url}'>Please complete start and end dates.</a>"
            application_errors.append(html)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Authorisation",
            "application_errors": application_errors,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/authorisation.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def start_authorisation(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")

        application.status = ImportApplication.PROCESSING
        application.save()

        return redirect(reverse("workbasket"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def cancel_authorisation(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        application.get_task(ImportApplication.PROCESSING, "process")

        application.status = ImportApplication.SUBMITTED
        application.save()

        return redirect(reverse("workbasket"))


def view_file(request, application, related_file_model, file_pk):
    has_perm_importer = request.user.has_perm("web.importer_access")
    has_perm_reference_data = request.user.has_perm("web.reference_data_access")

    if not has_perm_importer and not has_perm_reference_data:
        raise PermissionDenied

    # first check is for case managers (who are not marked as contacts of
    # importers), second is for people submitting applications
    if not has_perm_reference_data and not request.user.has_perm(
        "web.is_contact_of_importer", application.importer
    ):
        raise PermissionDenied

    document = related_file_model.get(pk=file_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


# TODO: Revisit these if we get around to ICMSLST-657
@login_required
@permission_required("web.importer_access", raise_exception=True)
def list_import_contacts(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "contacts": application.importcontact_set.all(),
            "page_title": "Open Individual Import Licence - Contacts",
        }

        return render(request, "web/domains/case/import/fa-import-contacts/list.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_import_contact(request: HttpRequest, pk: int, entity: str) -> HttpResponse:
    form_class = _get_entity_form(entity)

    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = form_class(data=request.POST, files=request.FILES)

            if form.is_valid():
                import_contact = form.save(commit=False)
                import_contact.import_application = application
                import_contact.entity = entity
                import_contact.save()

                # Assume known_bought_from is True if we are adding an import contact
                _update_know_bought_from(application)

                return redirect(
                    reverse(
                        "import:fa-edit-import-contact",
                        kwargs={
                            "application_pk": pk,
                            "entity": entity,
                            "contact_pk": import_contact.pk,
                        },
                    )
                )
        else:
            form = form_class()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence",
        }

        return render(request, "web/domains/case/import/fa-import-contacts/create.html", context)


def _update_know_bought_from(application: ImportApplication) -> None:
    # Map process types to the ImportApplication link to that class
    process_type_link = {
        OpenIndividualLicenceApplication.PROCESS_TYPE: "openindividuallicenceapplication",
        DFLApplication.PROCESS_TYPE: "dflapplication",
    }

    supported_types = Union[OpenIndividualLicenceApplication, DFLApplication]

    try:
        link = process_type_link[application.process_type]
    except KeyError:
        raise NotImplementedError(
            f"Unable to check know_bought_from: Unknown Firearm process_type: {application.process_type}"
        )

    # e.g. application.openindividuallicenceapplication to get access to OpenIndividualLicenceApplication
    firearms_application: supported_types = getattr(application, link)

    if not firearms_application.know_bought_from:
        firearms_application.know_bought_from = True
        firearms_application.save()


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_import_contact(
    request: HttpRequest, application_pk: int, entity: str, contact_pk: int
) -> HttpResponse:

    form_class = _get_entity_form(entity)

    with transaction.atomic():
        application = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        person = get_object_or_404(ImportContact, pk=contact_pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = form_class(data=request.POST, instance=person)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-edit-import-contact",
                        kwargs={
                            "application_pk": application_pk,
                            "entity": entity,
                            "contact_pk": contact_pk,
                        },
                    )
                )

        else:
            form = form_class(instance=person)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence - Edit Import Contact",
        }

        return render(request, "web/domains/case/import/fa-import-contacts/edit.html", context)


def _get_entity_form(
    entity: str,
) -> Type[Union[ImportContactLegalEntityForm, ImportContactPersonForm]]:

    if entity == ImportContact.LEGAL:
        form_class = ImportContactLegalEntityForm

    elif entity == ImportContact.NATURAL:
        form_class = ImportContactPersonForm

    else:
        raise NotImplementedError(f"View does not support entity type: {entity}")

    return form_class
