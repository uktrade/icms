import structlog as logging

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.template.models import Template
from web.notify.email import send_email
from web.views import ModelCreateView
from web.flow.models import Task

from .forms import (
    CloseCaseForm,
    NewExportApplicationForm,
    PrepareCertManufactureForm,
    SubmitCertManufactureForm,
)
from .models import ExportApplication, ExportApplicationType, CertificateOfManufactureApplication


logger = logging.get_logger(__name__)

permissions = "web.IMP_CERT_EDIT_APPLICATION"
export_case_officer_permission = "web.export_case_officer"


class ExportApplicationCreateView(ModelCreateView):
    template_name = "web/domains/case/export/create.html"
    model = ExportApplication
    success_url = reverse_lazy("home")
    cancel_url = reverse_lazy("home")
    form_class = NewExportApplicationForm
    page_title = "Create Certificate Application"
    permission_required = permissions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("form")

        if form:
            app_type = form["application_type"].data

            if app_type == str(ExportApplicationType.CERT_MANUFACTURE):
                msg = """Certificates of Manufacture are applicable only to
                pesticides that are for export only and not on free sale on the
                domestic market."""
            elif app_type == str(ExportApplicationType.CERT_FREE_SALE):
                msg = """If you are supplying the product to a client in the
                UK/EU then you do not require a certificate. Your client will
                need to apply for a certificate if they subsequently export it
                to one of their clients outside of the EU."""
            else:
                msg = None

            context["cert_msg"] = msg

        return context

    def get_form(self):
        if hasattr(self, "form"):
            return self.form

        if self.request.POST:
            self.form = NewExportApplicationForm(self.request, data=self.request.POST)
        else:
            self.form = NewExportApplicationForm(self.request)

        return self.form

    def post(self, request, *args, **kwargs):
        # see web/static/web/js/main.js::initialize
        if request.POST and request.POST.get("change", None):
            return super().get(request, *args, **kwargs)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            data = form.cleaned_data

            if data["application_type"].pk == ExportApplicationType.CERT_FREE_SALE:
                # TODO: implement for certificate of free sale
                raise Exception("Not implemented")
            elif data["application_type"].pk == ExportApplicationType.CERT_MANUFACTURE:
                model_class = CertificateOfManufactureApplication

            appl = model_class(
                process_type=model_class.PROCESS_TYPE,
                application_type=data["application_type"],
                exporter=data["exporter"],
                exporter_office=data["exporter_office"],
                created_by=self.request.user,
                last_updated_by=self.request.user,
                submitted_by=self.request.user,
            )
            appl.save()

            Task.objects.create(process=appl, task_type="prepare", owner=self.request.user)

            return redirect(reverse("export:com-edit", kwargs={"pk": appl.pk}))


@login_required
@permission_required(permissions, raise_exception=True)
def edit_com(request, pk):
    with transaction.atomic():
        appl = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=pk
        )

        task = appl.get_task(ExportApplication.IN_PROGRESS, "prepare")

        if request.POST:
            form = PrepareCertManufactureForm(data=request.POST, instance=appl)

            if form.is_valid():
                form.save()

                return redirect(reverse("export:com-submit", kwargs={"pk": pk}))

        else:
            form = PrepareCertManufactureForm(instance=appl, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": appl,
            "task": task,
            "form": form,
        }

        return render(request, "web/domains/case/export/prepare-com.html", context)


@login_required
@permission_required(permissions, raise_exception=True)
def submit_com(request, pk):
    with transaction.atomic():
        appl = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=pk
        )

        task = appl.get_task(ExportApplication.IN_PROGRESS, "prepare")

        if request.POST:
            form = SubmitCertManufactureForm(request, data=request.POST)
            go_back_to_edit = "_edit_application" in request.POST

            if go_back_to_edit:
                return redirect(reverse("export:com-edit", kwargs={"pk": pk}))

            if form.is_valid():
                appl.status = ExportApplication.SUBMITTED
                appl.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                # TODO: set owner when case processing workflow is done
                Task.objects.create(process=appl, task_type="process", previous=task)

                return redirect(reverse("home"))

        else:
            form = SubmitCertManufactureForm(request)

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": appl,
            "task": task,
            "exporter_name": appl.exporter.name,
            "form": form,
        }

        return render(request, "web/domains/case/export/submit-com.html", context)


@login_required
@permission_required(export_case_officer_permission, raise_exception=True)
@require_POST
def take_ownership(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ExportApplication.objects.select_for_update(), pk=pk)
        application.get_task(ExportApplication.SUBMITTED, "process")
        application.case_owner = request.user
        application.save()

    return redirect(reverse("workbasket"))


@login_required
@permission_required(export_case_officer_permission, raise_exception=True)
@require_POST
def release_ownership(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ExportApplication.objects.select_for_update(), pk=pk)
        application.get_task(ExportApplication.SUBMITTED, "process")
        application.case_owner = None
        application.save()

    return redirect(reverse("workbasket"))


@login_required
@permission_required(export_case_officer_permission, raise_exception=True)
def management(request, pk):
    with transaction.atomic():
        application = get_object_or_404(klass=ExportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ExportApplication.SUBMITTED, "process")
        form = CloseCaseForm()
        context = {
            "object": application,
            "task": task,
            "form": form,
        }
        if request.POST:
            application.status = ExportApplication.STOPPED
            application.save()

            task.is_active = False
            task.finished = timezone.now()
            task.save()

            if request.POST.get("send_email"):
                template = Template.objects.get(template_code="STOP_CASE")
                subject = template.get_title({"CASE_REFERENCE": application.pk})
                body = template.get_content({"CASE_REFERENCE": application.pk})
                recipients = [application.contact.email]
                recipients.extend(
                    application.exporter.baseteam_ptr.members.values_list("email", flat=True)
                )
                recipients = set(recipients)
                send_email(subject, body, recipients)

            return redirect(reverse("workbasket"))

    return render(
        request=request, template_name="web/domains/case/export/management.html", context=context
    )
