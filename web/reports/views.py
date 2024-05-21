from typing import Any, Union

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, RedirectView

from web.models import GeneratedReport, Report, ScheduleReport
from web.permissions import Perms, can_user_view_report
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3
from web.utils.spreadsheet import MIMETYPE

from .constants import ReportStatus, ReportType
from .forms import (
    BasicReportForm,
    ImportLicenceForm,
    IssuedCertificatesForm,
    ReportForm,
)
from .tasks import generate_report_task
from .utils import format_parameters_used, get_report_objects_for_user

ReportForms = Union[ImportLicenceForm, IssuedCertificatesForm, ReportForm]
ReportFormType = type[ReportForms]


class BaseReportView(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [Perms.sys.access_reports]

    def has_permission(self) -> bool:
        return super().has_permission() and can_user_view_report(
            self.request.user, self.get_report()
        )

    def get_report(self) -> Report:
        return get_object_or_404(Report, pk=self.kwargs["report_pk"])


class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = [Perms.sys.access_reports]
    template_name = "web/domains/reports/list-view.html"
    model = Report

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["page_title"] = "Reports"
        return context

    def get_queryset(self) -> QuerySet[Report]:
        return get_report_objects_for_user(self.request.user)


class RunHistoryListView(BaseReportView, ListView):
    template_name = "web/domains/reports/run-history-view.html"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[ScheduleReport]:
        queryset = ScheduleReport.objects.filter(report=self.get_report())
        if not self.request.GET.get("deleted"):
            queryset = queryset.exclude(status=ReportStatus.DELETED)
        return queryset.order_by("-finished_at")

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        report = self.get_report()
        context["report"] = report
        context["page_title"] = report.name
        context["showing_deleted"] = True if self.request.GET.get("deleted") else False
        return context


class RunOutputView(BaseReportView, DetailView):
    template_name = "web/domains/reports/run-output-view.html"
    pk_url_kwarg = "schedule_pk"
    model = ScheduleReport

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        report = self.get_report()
        context["page_title"] = report.name
        context["csv_files"] = self.object.generated_files.filter(
            document__content_type=MIMETYPE.CSV
        )
        context["xlsx_files"] = self.object.generated_files.filter(
            document__content_type=MIMETYPE.XLSX
        )
        context["parameters"] = format_parameters_used(self.object)
        return context


@method_decorator(transaction.atomic, name="post")
class RunReportView(BaseReportView, CreateView):
    template_name = "web/domains/reports/run-report.html"

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["report"] = self.report
        context["page_title"] = f"{self.report.name} - Run Report"
        return context

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.report = self.get_report()
        return super().get(request, *args, **kwargs)

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.report = self.get_report()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: ReportFormType) -> HttpResponseRedirect:
        scheduled_report = form.save(commit=False)
        scheduled_report.report = self.report
        scheduled_report.scheduled_by = self.request.user
        scheduled_report.status = ReportStatus.SUBMITTED
        form.cleaned_data.pop("title")
        form.cleaned_data.pop("notes")
        scheduled_report.parameters = form.cleaned_data
        scheduled_report.save()
        generate_report_task.delay(scheduled_report.pk)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("report:run-history-view", kwargs={"report_pk": self.report.pk})

    def get_form_class(self) -> ReportFormType:
        match self.report.report_type:
            case ReportType.ISSUED_CERTIFICATES:
                return IssuedCertificatesForm
            case ReportType.IMPORT_LICENCES:
                return ImportLicenceForm
            case ReportType.ACTIVE_USERS:
                return BasicReportForm
            case _:
                return ReportForm


class DownloadReportView(BaseReportView, DetailView):
    model = GeneratedReport
    pk_url_kwarg = "pk"

    def get(self, *args: Any, **kwargs: Any) -> HttpResponse:
        generated_report = GeneratedReport.objects.get(
            schedule__report=self.get_report(), pk=kwargs["pk"]
        )
        file_content = get_file_from_s3(generated_report.document.path)
        response = HttpResponse(
            content=file_content, content_type=generated_report.document.content_type
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{generated_report.document.filename}"'
        )
        return response


@method_decorator(transaction.atomic, name="post")
class DeleteReportView(BaseReportView, RedirectView):
    http_method_names = ["post"]

    def get_schedule_report(self) -> ScheduleReport:
        return get_object_or_404(ScheduleReport, pk=self.kwargs["schedule_pk"])

    def post(
        self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        schedule_report = self.get_schedule_report()
        schedule_report.status = ReportStatus.DELETED
        schedule_report.deleted_by = request.user
        schedule_report.deleted_at = timezone.now()
        schedule_report.save(update_fields=["status", "deleted_by", "deleted_at"])
        return HttpResponseRedirect(
            reverse("report:run-history-view", kwargs={"report_pk": schedule_report.report.pk})
        )
