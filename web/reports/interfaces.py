from datetime import datetime, timedelta
from typing import Any

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Model, OuterRef, QuerySet, Subquery, Value
from pydantic import BaseModel, ConfigDict, SerializeAsAny

from web.flow.models import ProcessTypes
from web.mail.constants import EmailTypes
from web.models import (
    CaseDocumentReference,
    CaseEmail,
    CFSSchedule,
    ExportApplication,
    ExportApplicationCertificate,
    ProductLegislation,
    ScheduleReport,
    UpdateRequest,
)
from web.models.shared import YesNoChoices

from .serializers import IssuedCertificateReportSerializer


class IssuedCertificateReportFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_type: str
    date_from: str
    date_to: str


ReportFilterT = type[IssuedCertificateReportFilter]
ReportSerializerT = type[IssuedCertificateReportSerializer]


class ReportResults(BaseModel):
    results: list[SerializeAsAny[BaseModel]]
    header: list[str]


class ReportInterface:
    """The reporting interface all reports must subclass."""

    ReportFilter: ReportFilterT
    ReportSerializer: ReportSerializerT

    def __init__(self, scheduled_report: ScheduleReport) -> None:
        self.scheduled_report = scheduled_report
        self.filters = self.ReportFilter(**self.scheduled_report.parameters)

    def get_data(self) -> dict[str, Any]:
        return ReportResults(
            results=[self.serialize_row(r) for r in self.get_queryset()],
            header=self.get_header(),
        ).model_dump(by_alias=True)

    def get_header(self) -> list[str]:
        schema = self.ReportSerializer.model_json_schema(by_alias=True, mode="serialization")
        return schema["required"]

    def serialize_row(self, r: Model) -> BaseModel:
        raise NotImplementedError

    def get_queryset(self) -> QuerySet:
        raise NotImplementedError


class IssuedCertificateReportInterface(ReportInterface):
    ReportSerializer = IssuedCertificateReportSerializer
    ReportFilter = IssuedCertificateReportFilter

    def get_queryset(self) -> QuerySet:
        queryset = CaseDocumentReference.objects.filter(
            document_type=CaseDocumentReference.Type.CERTIFICATE,
            export_application_certificates__status=ExportApplicationCertificate.Status.ACTIVE,
            export_application_certificates__case_completion_datetime__date__gte=self.filters.date_from,
            export_application_certificates__case_completion_datetime__date__lte=self.filters.date_to,
        )
        if self.filters.application_type:
            queryset = queryset.filter(
                export_application_certificates__export_application__application_type__type_code=self.filters.application_type
            )

        manufacturer_countries_sub_query = (
            CFSSchedule.objects.filter(
                application_id=OuterRef("export_application_certificates__export_application_id")
            )
            .order_by()
            .values("application")
            .annotate(
                manufacturer_countries_array=ArrayAgg(
                    "country_of_manufacture__name", distinct=True, default=Value([])
                )
            )
            .values("manufacturer_countries_array")
        )
        legislation_sub_query = (
            ProductLegislation.objects.filter(
                cfsschedule__application_id=OuterRef(
                    "export_application_certificates__export_application_id"
                )
            )
            .order_by()
            .values("cfsschedule__application_id")
            .annotate(legislation_array=ArrayAgg("name", distinct=True, default=Value([])))
            .values("legislation_array")
        )

        queryset = queryset.annotate(
            manufacturer_countries=Subquery(manufacturer_countries_sub_query),
            legislations=Subquery(legislation_sub_query),
        )
        return queryset.order_by("-reference")

    def serialize_row(self, cdr: CaseDocumentReference) -> ReportSerializer:  # type: ignore[valid-type]
        export_application = cdr.content_object.export_application.get_specific_model()
        is_cfs = export_application.process_type == ProcessTypes.CFS
        return self.ReportSerializer(
            certificate_reference=cdr.reference,
            case_reference=cdr.content_object.case_reference,
            application_type=export_application.application_type.type,
            submitted_datetime=export_application.submit_datetime,
            issue_datetime=cdr.content_object.case_completion_datetime,
            exporter=export_application.exporter.name,
            contact=export_application.contact.full_name,
            agent=export_application.agent.name if export_application.agent else "",
            country=cdr.reference_data.country.name,
            is_manufacturer=""
            if not is_cfs
            else self.get_is_manufacturer(export_application).title(),
            responsible_person_statement=""
            if not is_cfs
            else self.get_is_responsible_person(export_application).title(),
            countries_of_manufacture="" if not is_cfs else ",".join(cdr.manufacturer_countries),
            hse_email_count=export_application.case_emails.filter(
                template_code=EmailTypes.HSE_CASE_EMAIL
            )
            .exclude(status=CaseEmail.Status.DRAFT)
            .count(),
            beis_email_count=export_application.case_emails.filter(
                template_code=EmailTypes.BEIS_CASE_EMAIL
            )
            .exclude(status=CaseEmail.Status.DRAFT)
            .count(),
            application_update_count=export_application.update_requests.filter(
                status__in=[UpdateRequest.Status.CLOSED, UpdateRequest.Status.RESPONDED]
            ).count(),
            fir_count=export_application.further_information_requests.completed().count(),
            product_legislation="" if not is_cfs else ",".join(cdr.legislations),
            case_processing_time=self.get_total_processing_time(cdr, export_application),
            total_processing_time=self.get_total_processing_time(cdr, export_application),
            business_days_to_process=self.get_business_days_to_process(cdr, export_application),
        )

    def get_is_responsible_person(self, export_application: ExportApplication) -> YesNoChoices:
        if export_application.schedules.filter(
            schedule_statements_is_responsible_person=True
        ).exists():
            return YesNoChoices.yes
        return YesNoChoices.no

    def get_is_manufacturer(self, export_application: ExportApplication) -> YesNoChoices:
        if export_application.schedules.filter(
            exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER
        ):
            return YesNoChoices.yes
        return YesNoChoices.no

    def get_total_processing_time(
        self, cdr: CaseDocumentReference, export_application: ExportApplication
    ) -> str:
        return self._format_time_delta(
            cdr.content_object.case_completion_datetime, export_application.submit_datetime
        )

    def _format_time_delta(self, from_datetime: datetime, to_datetime: datetime) -> str:
        time_delta = from_datetime - to_datetime
        hours = time_delta.seconds // 3600
        minutes = (time_delta.seconds % 3600) // 60
        return f"{time_delta.days}d {hours}h {minutes}m"

    def get_business_days_to_process(
        self, cdr: CaseDocumentReference, export_application: ExportApplication
    ) -> int:
        start = export_application.submit_datetime.date()
        end = cdr.content_object.case_completion_datetime.date()
        date_diff = end - start
        business_days = 0

        for i in range(date_diff.days + 1):
            day = start + timedelta(days=i)
            if day.weekday() < 5:
                business_days += 1

        return business_days
