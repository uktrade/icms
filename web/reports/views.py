from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from web.models import GeneratedReport, Report, ScheduleReport
from web.permissions import Perms
from web.utils.s3 import get_file_from_s3
from web.utils.spreadsheet import MIMETYPE

from .constants import ReportStatus, ReportType
from .forms import IssuedCertificatesForm, ReportForm
from .tasks import generate_report_task


class BaseReportView(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = [Perms.page.view_reports]

    def get_report(self) -> Report:
        return get_object_or_404(Report, pk=self.kwargs["report_pk"])


class ReportListView(BaseReportView, ListView):
    template_name = "web/domains/reports/list-view.html"
    model = Report

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["page_title"] = "Reports"
        return context


class RunHistoryListView(BaseReportView, ListView):
    template_name = "web/domains/reports/run-history-view.html"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return ScheduleReport.objects.filter(report=self.get_report()).order_by("-finished_at")

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        report = self.get_report()
        context["report"] = report
        context["page_title"] = report.name
        return context


class RunOutputView(BaseReportView, DetailView):
    template_name = "web/domains/reports/run-output-view.html"
    pk_url_kwarg = "schedule_pk"
    model = ScheduleReport

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        report = self.get_report()
        context["page_title"] = report.name
        context["csv_files"] = self.object.generated_files.filter(
            document__content_type=MIMETYPE.CSV
        )
        context["xlsx_files"] = self.object.generated_files.filter(
            document__content_type=MIMETYPE.XLSX
        )
        return context


class RunReportView(BaseReportView, CreateView):
    permission_required = [Perms.page.view_reports, Perms.sys.generate_reports]  # type: ignore[list-item]
    template_name = "web/domains/reports/run-report.html"

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["report"] = self.report
        context["page_title"] = f"{self.report.name} - Run Report"
        return context

    def get(self, request, *args, **kwargs):
        self.report = self.get_report()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.report = self.get_report()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponseRedirect:
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
        return reverse("run-history-view", kwargs={"report_pk": self.report.pk})

    def get_form_class(self):
        if self.report.report_type == ReportType.ISSUED_CERTIFICATES:
            return IssuedCertificatesForm
        return ReportForm


class DownloadReportView(BaseReportView, DetailView):
    model = GeneratedReport
    pk_url_kwarg = "pk"

    def get(self, *args, **kwargs) -> HttpResponse:
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
