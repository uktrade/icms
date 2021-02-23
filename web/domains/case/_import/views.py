from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from guardian.shortcuts import get_users_with_perms

from web.domains.case.forms import CloseCaseForm
from web.domains.template.models import Template
from web.flow.models import Task
from web.notify.email import send_email

from .firearms.models import OpenIndividualLicenceApplication
from .forms import CreateImportApplicationForm, WithdrawForm, WithdrawResponseForm
from .models import ImportApplication, ImportApplicationType, WithdrawImportApplication
from .sanctions.models import SanctionsAndAdhocApplication
from .wood.models import WoodQuotaApplication


class ImportApplicationChoiceView(TemplateView, PermissionRequiredMixin):
    template_name = "web/domains/case/import/choice.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_sanctions(request):
    import_application_type = ImportApplicationType.TYPE_SANCTION_ADHOC
    model_class = SanctionsAndAdhocApplication
    redirect_view = "import:edit-sanctions-and-adhoc-licence-application"
    return _create_application(request, import_application_type, model_class, redirect_view)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_oil(request):
    import_application_type = ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE
    model_class = OpenIndividualLicenceApplication
    redirect_view = "import:edit-oil"
    return _create_application(request, import_application_type, model_class, redirect_view)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_wood_quota(request):
    import_application_type = ImportApplicationType.TYPE_WOOD_QUOTA
    model_class = WoodQuotaApplication
    redirect_view = "import:edit-wood-quota"
    return _create_application(request, import_application_type, model_class, redirect_view)


def _create_application(request, import_application_type, model_class, redirect_view):
    import_application_type = ImportApplicationType.objects.get(
        Q(type=import_application_type) | Q(sub_type=import_application_type)
    )

    if request.POST:
        form = CreateImportApplicationForm(request.user, request.POST)
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
        form = CreateImportApplicationForm(request.user)

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
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Management",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_withdrawals(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
        )
        withdrawals = application.withdrawals.filter(is_active=True)
        current_withdrawal = withdrawals.filter(
            status=WithdrawImportApplication.STATUS_OPEN
        ).first()

        if request.POST:
            form = WithdrawResponseForm(request.POST, instance=current_withdrawal)
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
            form = WithdrawResponseForm(instance=current_withdrawal)

        context = {
            "process": application,
            "task": task,
            "page_title": f"{application.application_type.get_type_description()} - Withdrawals",
            "form": form,
            "withdrawals": withdrawals,
            "current_withdrawal": current_withdrawal,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/withdrawals.html",
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
            form = WithdrawForm(request.POST)
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
            form = WithdrawForm()

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
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
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
            [ImportApplication.SUBMITTED, ImportApplication.WITHDRAWN], "process"
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
