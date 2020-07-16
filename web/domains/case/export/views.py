import structlog as logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import generic

from web.views import ModelCreateView
from web.flow.models import Task

from .forms import NewExportApplicationForm
from .models import ExportApplication, ExportApplicationType, CertificateOfManufactureApplication

from . import forms

logger = logging.get_logger(__name__)

permissions = "web.IMP_CERT_EDIT_APPLICATION"


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

            return redirect(reverse("export:com_edit", kwargs={"pk": appl.pk}))


# FIXME: split into view_com / edit_com, make function-based
class PrepareCertManufactureView(PermissionRequiredMixin, generic.UpdateView):
    model = CertificateOfManufactureApplication
    form_class = forms.PrepareCertManufactureForm
    template_name = "web/domains/case/export/prepare-com.html"
    process_template = "web/domains/case/export/partials/process.html"
    permission_required = permissions

    # FIXME: get/post need to do the same checks as get_context_data is doing?

    def get_success_url(self):
        return reverse("export:com_submit", kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        process = self.get_object()
        task = process.get_task(ExportApplication.IN_PROGRESS, "prepare")

        context = super().get_context_data(**kwargs)

        context["process_template"] = self.process_template
        context["process"] = process
        context["task"] = task

        return context

    def get_form(self):
        if self.request.POST:
            form = self.form_class(
                self.request, data=self.request.POST, instance=self.get_object(),
            )
        else:
            form = self.form_class(
                self.request, instance=self.get_object(), initial={"contact": self.request.user},
            )

        return form


# FIXME: make function-based, rename submit_com
class SubmitCertManufactureView(PermissionRequiredMixin, generic.UpdateView):
    model = CertificateOfManufactureApplication
    template_name = "web/domains/case/export/submit-com.html"
    form_class = forms.SubmitCertManufactureForm
    process_template = "web/domains/case/export/partials/process.html"
    permission_required = permissions
    success_url = reverse_lazy("home")

    def post(self, request, *args, **kwargs):
        go_back_to_edit = "_edit_application" in request.POST

        if go_back_to_edit:
            return redirect(reverse("export:com_edit", kwargs={"pk": kwargs["pk"]}))

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        process = self.get_object()
        task = process.get_task(ExportApplication.IN_PROGRESS, "prepare")

        with transaction.atomic():
            process.status = ExportApplication.SUBMITTED
            process.save()

            task.is_active = False
            task.finished = timezone.now()
            task.save()

            # TODO: set owner when case processing workflow is done
            Task.objects.create(process=process, task_type="process", previous=task)

        return HttpResponseRedirect(self.get_success_url())

    def get_form(self):
        if self.request.POST:
            form = self.form_class(self.request, data=self.request.POST)
        else:
            form = self.form_class(self.request)

        return form

    # FIXME: get/post need to do the same checks as get_context_data is doing?

    def get_context_data(self, **kwargs):
        process = self.get_object()
        task = process.get_task(ExportApplication.IN_PROGRESS, "prepare")

        context = super().get_context_data(**kwargs)

        context["process_template"] = self.process_template
        context["process"] = process
        context["task"] = task

        context["exporter_name"] = process.exporter.name

        return context
