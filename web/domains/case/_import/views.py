import weasyprint
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import get_users_with_perms
from s3chunkuploader.file_handler import s3_client

from web.domains.case.forms import CloseCaseForm
from web.domains.importer.models import Importer
from web.domains.template.models import Template
from web.flow.models import Task
from web.notify.email import send_email

from .. import views as case_views
from . import forms
from .derogations.models import DerogationsApplication
from .firearms.models import OpenIndividualLicenceApplication
from .models import ImportApplication, ImportApplicationType, WithdrawImportApplication
from .sanctions.models import SanctionsAndAdhocApplication
from .wood.models import WoodQuotaApplication


class ImportApplicationChoiceView(TemplateView, PermissionRequiredMixin):
    template_name = "web/domains/case/import/choice.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_derogations(request):
    import_application_type = ImportApplicationType.TYPE_DEGROGATION_FROM_SANCTIONS_BAN
    model_class = DerogationsApplication
    redirect_view = "import:derogations:edit-derogations"
    return _create_application(request, import_application_type, model_class, redirect_view)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sanctions(request):
    import_application_type = ImportApplicationType.TYPE_SANCTION_ADHOC
    model_class = SanctionsAndAdhocApplication
    redirect_view = "import:sanctions:edit-sanctions-and-adhoc-licence-application"
    return _create_application(request, import_application_type, model_class, redirect_view)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_oil(request):
    import_application_type = ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE
    model_class = OpenIndividualLicenceApplication
    redirect_view = "import:firearms:edit-oil"
    return _create_application(request, import_application_type, model_class, redirect_view)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_wood_quota(request):
    import_application_type = ImportApplicationType.TYPE_WOOD_QUOTA
    model_class = WoodQuotaApplication
    redirect_view = "import:wood:edit-quota"
    return _create_application(request, import_application_type, model_class, redirect_view)


def _create_application(request, import_application_type, model_class, redirect_view):
    import_application_type = ImportApplicationType.objects.get(
        Q(type=import_application_type) | Q(sub_type=import_application_type)
    )

    if request.POST:
        form = forms.CreateImportApplicationForm(request.user, request.POST)
        if form.is_valid():
            application = model_class()
            application.importer = form.cleaned_data["importer"]
            application.importer_office = form.cleaned_data["importer_office"]
            application.process_type = model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = import_application_type

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)
            return redirect(reverse(redirect_view, kwargs={"pk": application.pk}))
    else:
        form = forms.CreateImportApplicationForm(request.user)

    context = {"form": form, "import_application_type": import_application_type}
    return render(request, "web/domains/case/import/create.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def take_ownership(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
        application.get_task([ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process")
        application.case_owner = request.user
        application.save()

        return redirect(reverse("workbasket"))


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
def view_case(request, pk):
    has_perm_importer = request.user.has_perm("web.importer_access")
    has_perm_reference_data = request.user.has_perm("web.reference_data_access")
    if not has_perm_importer and not has_perm_reference_data:
        raise PermissionDenied

    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(
            [
                ImportApplication.SUBMITTED,
                ImportApplication.WITHDRAWN,
                ImportApplication.PROCESSING,
            ],
            "process",
        )

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": application.application_type.get_type_description(),
        }
        return render(request, "web/domains/case/import/view.html", context)


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
def edit_note(request, application_pk, note_pk):
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
@require_POST
def archive_note_file(request, application_pk, note_pk, file_pk):
    return case_views._archive_note_file(
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
    return case_views._list_update_requests(request, pk, ImportApplication, "import")


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def start_update_request(request, application_pk, update_request_pk):
    return case_views._start_update_request(
        request, application_pk, update_request_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def respond_update_request(request, application_pk, update_request_pk):
    # TODO: make url more generic
    return case_views._respond_update_request(
        request, application_pk, update_request_pk, ImportApplication, "import"
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_firs(request, application_pk):
    extra_context = {"show_firs": True}
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

    return case_views._edit_fir(
        request, application_pk, fir_pk, ImportApplication, "import", importer_contacts
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
def prepare_response(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ImportApplication.objects.select_for_update(), pk=pk)
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
            "process": application,
            "task": task,
            "page_title": "Response Preparation",
            "form": form,
            "goods_template": "web/domains/case/import/partials/firearms/oil-goods.html",
            "documents_template": "web/domains/case/import/partials/firearms/oil-documents.html",
            "cover_letter_flag": application.application_type.cover_letter_flag,
            "electronic_licence_flag": application.application_type.electronic_licence_flag,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/prepare-response.html",
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
                url = reverse("import:firearms:manage-checklist", args=[application.pk])
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


def _view_file(request, application, related_file_model, file_pk):
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

    client = s3_client()

    s3_file = client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=document.path)
    s3_file_content = s3_file["Body"].read()

    response = HttpResponse(content=s3_file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response
