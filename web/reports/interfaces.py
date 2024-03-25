from itertools import chain
from typing import Any, ClassVar, final

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Model, OuterRef, Q, QuerySet, Subquery, Value
from pydantic import BaseModel, ConfigDict, SerializeAsAny

from web.domains.case._import.fa.types import (
    FaImportApplication,
    FaSupplementaryReport,
    ReportFirearms,
)
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpAccessOrExpAccess
from web.flow.models import ProcessTypes
from web.mail.constants import EmailTypes
from web.models import (
    AccessRequest,
    CaseDocumentReference,
    CaseEmail,
    CFSSchedule,
    ExportApplication,
    ExportApplicationCertificate,
    ExporterAccessRequest,
    ImportApplication,
    ImporterAccessRequest,
    ProductLegislation,
    ScheduleReport,
    UpdateRequest,
)
from web.models.shared import YesNoChoices
from web.utils.pdf.utils import _get_fa_dfl_goods, _get_fa_sil_goods

from . import utils
from .constants import DateFilterType
from .serializers import (
    AccessRequestTotalsReportSerializer,
    DFLFirearmsLicenceSerializer,
    ExporterAccessRequestReportSerializer,
    ImporterAccessRequestReportSerializer,
    ImportLicenceSerializer,
    IssuedCertificateReportSerializer,
    OILFirearmsLicenceSerializer,
    SILFirearmsLicenceSerializer,
    SupplementaryFirearmsSerializer,
)


class IssuedCertificateReportFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_type: str
    date_from: str
    date_to: str
    legislation: list[int]


class ImportLicenceFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    application_type: str
    date_filter_type: DateFilterType
    date_from: str
    date_to: str


class BasicReportFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date_from: str
    date_to: str


class ReportResults(BaseModel):
    results: list[SerializeAsAny[BaseModel]]
    header: list[str]


class ReportInterface:
    """The reporting interface all reports must subclass."""

    ReportFilter: ClassVar[type[BaseModel]]
    ReportSerializer: ClassVar[type[BaseModel]]
    name: ClassVar[str]

    def __init__(self, scheduled_report: ScheduleReport) -> None:
        self.scheduled_report = scheduled_report
        self.filters = self.ReportFilter(**self.scheduled_report.parameters)

    def get_data(self) -> dict[str, Any]:
        return ReportResults(
            results=self.process_results(),
            header=self.get_header(),
        ).model_dump(by_alias=True)

    def process_results(self) -> list[BaseModel]:
        results = []
        for r in self.get_queryset():
            results += self.serialize_rows(r)
        return results

    def get_header(self) -> list[str]:
        schema = self.ReportSerializer.model_json_schema(by_alias=True, mode="serialization")
        return schema["required"]

    def serialize_rows(self, r: Model) -> list:
        return [self.serialize_row(r)]

    def serialize_row(self, *args, **kwargs) -> BaseModel:
        raise NotImplementedError

    def get_queryset(self) -> QuerySet:
        raise NotImplementedError


class BaseFirearmsLicenceInterface(ReportInterface):
    ReportFilter = BasicReportFilter
    filters: BasicReportFilter

    def get_application_filter(self) -> Q:
        raise NotImplementedError

    def get_queryset(self) -> QuerySet:
        _filter = Q(
            licences__case_completion_datetime__date__range=(
                self.filters.date_from,
                self.filters.date_to,
            )
        )
        return ImportApplication.objects.filter(
            _filter,
            self.get_application_filter(),
            decision=ImportApplication.APPROVE,
            status__in=[ImpExpStatus.COMPLETED, ImpExpStatus.REVOKED],
            licences__document_references__reference__isnull=False,
        ).order_by("reference")

    def serialize_row(self, import_application: ImportApplication):
        ia = import_application.get_specific_model()
        licence = utils.get_licence_details(ia)
        return self.ReportSerializer(
            licence_reference=licence.reference,
            variation_number=utils.get_variation_number(ia),
            case_reference=ia.get_reference(),
            importer=ia.importer.display_name,
            eori_number=ia.importer.eori_number,
            importer_address=utils.get_importer_address(ia),
            first_submitted_date=ia.submit_datetime.date(),
            final_submitted_date=ia.last_submit_datetime.date(),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            country_of_origin=getattr(ia.origin_country, "name", ""),
            country_of_consignment=getattr(ia.consignment_country, "name", ""),
            endorsements="\n".join(ia.endorsements.values_list("content", flat=True)),
            revoked=ia.status == ImportApplication.Statuses.REVOKED,
            **self.extra_fields(ia),
        )

    def extra_fields(self, ia: FaImportApplication) -> dict[str, Any]:
        raise NotImplementedError


@final
class IssuedCertificateReportInterface(ReportInterface):
    ReportSerializer = IssuedCertificateReportSerializer
    ReportFilter = IssuedCertificateReportFilter
    name = "Issued Certificates"

    # Added to fix typing
    filters: IssuedCertificateReportFilter

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.legislations = dict(ProductLegislation.objects.values_list("pk", "name"))

    def get_queryset(self) -> QuerySet:
        queryset = CaseDocumentReference.objects.filter(
            document_type=CaseDocumentReference.Type.CERTIFICATE,
            export_application_certificates__status=ExportApplicationCertificate.Status.ACTIVE,
            export_application_certificates__case_completion_datetime__date__range=(
                self.filters.date_from,
                self.filters.date_to,
            ),
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
            .annotate(legislation_array=ArrayAgg("pk", distinct=True, default=Value([])))
            .values("legislation_array")
        )

        queryset = queryset.annotate(
            manufacturer_countries=Subquery(manufacturer_countries_sub_query),
            legislations=Subquery(legislation_sub_query),
        )

        if self.filters.legislation:
            queryset = queryset.filter(legislations__contains=self.filters.legislation)
        return queryset.order_by("-reference")

    def serialize_row(self, cdr: CaseDocumentReference) -> IssuedCertificateReportSerializer:
        export_application = cdr.content_object.export_application.get_specific_model()
        is_cfs = export_application.process_type == ProcessTypes.CFS

        return IssuedCertificateReportSerializer(
            certificate_reference=cdr.reference,
            case_reference=cdr.content_object.case_reference,
            application_type=export_application.application_type.type,
            submitted_datetime=export_application.submit_datetime,
            issue_datetime=cdr.content_object.case_completion_datetime,
            exporter=export_application.exporter.name,
            contact_full_name=export_application.contact.full_name,
            agent=export_application.agent.name if export_application.agent else "",
            country=cdr.reference_data.country.name,
            is_manufacturer=(
                "" if not is_cfs else self.get_is_manufacturer(export_application).title()
            ),
            responsible_person_statement=(
                "" if not is_cfs else self.get_is_responsible_person(export_application).title()
            ),
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
            product_legislation=(
                "" if not is_cfs else ", ".join([self.legislations[pk] for pk in cdr.legislations])
            ),
            case_processing_time=self.get_total_processing_time(cdr, export_application),
            total_processing_time=self.get_total_processing_time(cdr, export_application),
            business_days_to_process=self.get_business_days_to_process(cdr, export_application),
            continent=cdr.reference_data.country.overseas_region.name,
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
        return utils.format_time_delta(
            cdr.content_object.case_completion_datetime, export_application.submit_datetime
        )

    def get_business_days_to_process(
        self, cdr: CaseDocumentReference, export_application: ExportApplication
    ) -> int:
        start_date = export_application.submit_datetime.date()
        end_date = cdr.content_object.case_completion_datetime.date()
        return utils.get_business_days(start_date, end_date)


class ImporterAccessRequestInterface(ReportInterface):
    ReportSerializer = ImporterAccessRequestReportSerializer
    ReportFilter = BasicReportFilter
    filters: BasicReportFilter
    model: Model = ImporterAccessRequest
    name = "Importer Access Requests"

    def get_queryset(self) -> QuerySet:
        return self.model.objects.filter(
            response__isnull=False,
            submit_datetime__date__range=(self.filters.date_from, self.filters.date_to),
        ).order_by("-submit_datetime")

    def serialize_row(self, ar: ImpAccessOrExpAccess) -> ImporterAccessRequestReportSerializer:
        is_agent = ar.is_agent_request
        request_type = f"{ar.REQUEST_TYPE.title()} Access Request"
        return self.ReportSerializer(
            request_date=ar.submit_datetime.date(),
            request_type=f"Agent {request_type}" if is_agent else request_type,
            name=ar.organisation_name,
            address=ar.organisation_address.replace("\r", ""),
            agent_name=ar.agent_name if is_agent else "",
            agent_address=ar.agent_address.replace("\r", "") if is_agent else "",
            response=ar.get_response_display(),
            response_reason=ar.response_reason,
        )


@final
class ExporterAccessRequestInterface(ImporterAccessRequestInterface):
    ReportSerializer = ExporterAccessRequestReportSerializer
    model: Model = ExporterAccessRequest
    name = "Exporter Access Requests"


@final
class AccessRequestTotalsInterface(ReportInterface):
    name = "Access Requests Totals"
    ReportFilter = BasicReportFilter
    filters: BasicReportFilter
    ReportSerializer = AccessRequestTotalsReportSerializer

    def get_queryset(self) -> QuerySet:
        return (
            AccessRequest.objects.filter(
                response__isnull=False,
                submit_datetime__date__range=(self.filters.date_from, self.filters.date_to),
            )
            .values("response")
            .annotate(total=Count("id"))
            .order_by()
        )

    def process_results(self) -> list[BaseModel]:
        data = {}
        for r in self.get_queryset():
            data[r["response"]] = r["total"]
        approved = data.get("APPROVED", 0)
        refused = data.get("REFUSED", 0)
        return [
            self.ReportSerializer(
                total_requests=approved + refused,
                approved_requests=approved,
                refused_requests=refused,
            )
        ]


@final
class ImportLicenceInterface(ReportInterface):
    name = "Import Licence Data Extract"
    ReportSerializer = ImportLicenceSerializer
    ReportFilter = ImportLicenceFilter
    filters: ImportLicenceFilter

    def get_queryset(self) -> QuerySet:
        if self.filters.date_filter_type == DateFilterType.SUBMITTED:
            _filter = Q(submit_datetime__date__range=(self.filters.date_from, self.filters.date_to))
        else:
            _filter = Q(
                licences__case_completion_datetime__date__range=(
                    self.filters.date_from,
                    self.filters.date_to,
                )
            )

        queryset = (
            ImportApplication.objects.filter(
                _filter,
                status__in=[ImpExpStatus.COMPLETED, ImpExpStatus.WITHDRAWN, ImpExpStatus.REVOKED],
            )
            .order_by("-reference")
            .distinct()
        )
        if self.filters.application_type:
            queryset = queryset.filter(application_type__type=self.filters.application_type)
        return queryset

    def serialize_row(self, import_application: ImportApplication) -> ImportLicenceSerializer:
        ia = import_application.get_specific_model()
        is_adhoc = import_application.process_type == ProcessTypes.SANCTIONS
        is_sps = import_application.process_type == ProcessTypes.SPS
        licence = utils.get_licence_details(ia)

        return self.ReportSerializer(
            case_reference=ia.get_reference(),
            licence_reference=licence.reference,
            licence_type=licence.licence_type,
            under_appeal="",  # Unused field in V1
            ima_type=ia.application_type.type,
            ima_type_title=ia.application_type.get_type_display(),
            ima_sub_type=ia.application_type.sub_type,
            ima_sub_type_title=ia.application_type.get_sub_type_display(),
            variation_number=utils.get_variation_number(ia),
            status=ia.status,
            importer=ia.importer.display_name,
            agent_name=ia.agent.name if ia.agent else None,
            app_contact_name=getattr(ia.contact, "full_name", ""),
            country_of_origin=getattr(ia.origin_country, "name", ""),
            country_of_consignment=getattr(ia.consignment_country, "name", ""),
            shipping_year=getattr(ia, "shipping_year", ""),
            com_group_name=self.get_com_group_name(import_application),
            commodity_codes=self.get_commodity_codes(import_application, is_adhoc, is_sps),
            initial_submitted_datetime=ia.submit_datetime,
            initial_case_closed_datetime=licence.initial_case_closed_datetime,
            time_to_initial_close=licence.time_to_initial_close,
            latest_case_closed_datetime=licence.latest_case_closed_datetime,
            licence_dates=utils.get_licence_dates(licence),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            importer_printable=ia.application_type.importer_printable,
        )

    def get_com_group_name(self, import_application: ImportApplication) -> str:
        ia = import_application.get_specific_model()
        if not ia.commodity_group or not ia.commodity_group.group_name:
            return ""
        return ia.commodity_group.group_name

    def get_commodity_codes(
        self, import_application: ImportApplication, is_adhoc: bool, is_sps: bool
    ) -> str:
        ia = import_application.get_specific_model()
        if is_sps and ia.commodity:
            return f"Code: {ia.commodity.commodity_code}"

        if not is_adhoc:
            return ""

        details = []
        for goods in ia.sanctions_goods.order_by("-commodity"):
            if goods.commodity:
                details.append(f"Code: {goods.commodity}; Desc: {goods.goods_description}")
        return ", ".join(details)


@final
class SupplementaryFirearmsInterface(ReportInterface):
    name = "Supplementary firearms report"
    ReportSerializer = SupplementaryFirearmsSerializer
    ReportFilter = BasicReportFilter
    filters: BasicReportFilter

    def get_queryset(self) -> QuerySet:
        _filter = Q(
            licences__case_completion_datetime__date__range=(
                self.filters.date_from,
                self.filters.date_to,
            )
        )
        return (
            ImportApplication.objects.filter(
                _filter,
                Q(silapplication__supplementary_info__isnull=False)
                | Q(openindividuallicenceapplication__supplementary_info__isnull=False)
                | Q(dflapplication__supplementary_info__isnull=False),
            )
            .exclude(status__in=[ImpExpStatus.IN_PROGRESS, ImpExpStatus.DELETED])
            .order_by("-reference")
        )

    def serialize_rows(self, import_application: ImportApplication) -> list:
        results = []
        ia = import_application.get_specific_model()
        for report in ia.supplementary_info.reports.all():
            for report_firearms in chain(
                report.get_report_firearms(is_manual=True),
                report.get_report_firearms(is_upload=True),
                report.get_report_firearms(is_no_firearm=True),
            ):
                results.append(self.serialize_row(report_firearms, ia))
        return results

    def serialize_row(
        self, s: ReportFirearms, ia: FaImportApplication
    ) -> SupplementaryFirearmsSerializer:
        is_dfl = ia.process_type == ProcessTypes.FA_DFL
        is_sil = ia.process_type == ProcessTypes.FA_SIL
        is_oil = ia.process_type == ProcessTypes.FA_OIL

        report: FaSupplementaryReport = s.report

        licence = utils.get_licence_details(ia)

        if report.bought_from:
            bought_from_name = str(report.bought_from)
            bought_from_reg_no = report.bought_from.registration_number
            bought_from_address = report.bought_from.address or ""
        else:
            bought_from_name = ""
            bought_from_reg_no = ""
            bought_from_address = ""

        if is_oil:
            goods_certificate = None
        else:
            goods_certificate = s.goods_certificate

        if is_dfl:
            goods_quantity = 1
        else:
            goods_quantity = goods_certificate.quantity or 0 if goods_certificate else 0

        exceed_quantity = is_sil and getattr(goods_certificate, "unlimited_quantity", False)

        return self.ReportSerializer(
            licence_reference=licence.reference,
            case_reference=ia.get_reference(),
            case_type=ia.application_type.sub_type,
            importer=ia.importer.display_name,
            eori_number=ia.importer.eori_number,
            importer_address=utils.get_importer_address(ia),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            country_of_origin=getattr(ia.origin_country, "name", ""),
            country_of_consignment=getattr(ia.consignment_country, "name", ""),
            endorsements="\n".join(ia.endorsements.values_list("content", flat=True)),
            report_date=report.date_received,
            constabularies=utils.get_constabularies(ia),
            who_bought_from_name=bought_from_name,
            who_bought_from_reg_no=bought_from_reg_no,
            who_bought_from_address=bought_from_address,
            frame_serial_number=s.serial_number,
            means_of_transport=report.transport,
            date_firearms_received=report.date_received,
            calibre=s.calibre,
            proofing=s.proofing.title() if s.proofing else "",
            make_model=s.model,
            firearms_document="See uploaded files on report" if s.document else "",
            all_reported=report.supplementary_info.is_complete,
            goods_description=s.get_description(),
            goods_quantity=goods_quantity,
            firearms_exceed_quantity=exceed_quantity,
            goods_description_with_subsection=s.get_description(),
        )


@final
class DFLFirearmsLicenceInterface(BaseFirearmsLicenceInterface):
    name = "Deactivated Firearms Licences"
    ReportSerializer = DFLFirearmsLicenceSerializer

    def get_application_filter(self) -> Q:
        return Q(dflapplication__isnull=False)

    def extra_fields(self, ia: FaImportApplication) -> dict[str, Any]:
        return {
            "goods_description": "\n".join(_get_fa_dfl_goods(ia)),
        }


@final
class OILFirearmsLicenceInterface(BaseFirearmsLicenceInterface):
    name = "Open Firearms Licences"
    ReportSerializer = OILFirearmsLicenceSerializer

    def get_application_filter(self) -> Q:
        return Q(openindividuallicenceapplication__isnull=False)

    def extra_fields(self, ia: FaImportApplication) -> dict[str, Any]:
        constabulary_email_times = utils.get_constabulary_email_times(ia)
        return {
            "constabularies": utils.get_constabularies(ia),
            "first_constabulary_email_sent_date": constabulary_email_times.first_email_sent,
            "last_constabulary_email_closed_date": constabulary_email_times.last_email_closed,
        }


@final
class SILFirearmsLicenceInterface(BaseFirearmsLicenceInterface):
    name = "Specific Firearms Licences"
    ReportSerializer = SILFirearmsLicenceSerializer

    def get_application_filter(self) -> Q:
        return Q(silapplication__isnull=False)

    def extra_fields(self, ia: FaImportApplication) -> dict[str, Any]:
        constabulary_email_times = utils.get_constabulary_email_times(ia)
        descriptions = []
        for desc, quantity in _get_fa_sil_goods(ia):
            descriptions.append(f"{quantity} x {desc}")

        return {
            "constabularies": utils.get_constabularies(ia),
            "goods_description": "\n".join(descriptions),
            "first_constabulary_email_sent_date": constabulary_email_times.first_email_sent,
            "last_constabulary_email_closed_date": constabulary_email_times.last_email_closed,
        }
