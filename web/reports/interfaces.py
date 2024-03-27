import datetime as dt
from itertools import chain
from typing import Any, ClassVar, final

from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Count, F, Model, OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import JSONObject
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
    FurtherInformationRequest,
    ImportApplication,
    ImportApplicationType,
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
        for r in self.get_queryset().iterator(500):
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
        return (
            ImportApplication.objects.filter(
                _filter,
                self.get_application_filter(),
                decision=ImportApplication.APPROVE,
                status__in=[ImpExpStatus.COMPLETED, ImpExpStatus.REVOKED],
                licences__document_references__reference__isnull=False,
            )
            .annotate(
                country_of_origin=F("origin_country__name"),
                country_of_consignment=F("consignment_country__name"),
                application_sub_type=F("application_type__sub_type"),
                endorsement_list=ArrayAgg(
                    "endorsements__content",
                    distinct=True,
                    filter=Q(endorsements__isnull=False),
                    default=Value([]),
                ),
            )
            .select_related("importer", "importer_office")
            .prefetch_related("licences")
            .order_by("reference")
        )

    def serialize_row(self, import_application: ImportApplication):
        ia = import_application.get_specific_model()
        licence = utils.get_licence_details(ia)
        return self.ReportSerializer(
            licence_reference=licence.reference,
            variation_number=utils.get_variation_number(ia.reference),
            case_reference=ia.get_reference(),
            importer=ia.importer.display_name,
            eori_number=ia.importer.eori_number,
            importer_address=utils.get_importer_address(ia),
            first_submitted_date=ia.submit_datetime.date(),
            final_submitted_date=ia.last_submit_datetime.date(),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            country_of_origin=import_application.country_of_origin,
            country_of_consignment=import_application.country_of_consignment,
            endorsements="\n".join(import_application.endorsement_list),
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

    def get_export_application_query(self) -> QuerySet:
        return (
            ExportApplication.objects.filter(
                pk=OuterRef("export_application_certificates__export_application_id")
            )
            .annotate(
                hse_email_count=Count(
                    "case_emails",
                    filter=Q(
                        Q(case_emails__template_code=EmailTypes.HSE_CASE_EMAIL),
                        ~Q(case_emails__status=CaseEmail.Status.DRAFT),
                    ),
                    distinct=True,
                ),
                beis_email_count=Count(
                    "case_emails",
                    filter=Q(
                        Q(case_emails__template_code=EmailTypes.BEIS_CASE_EMAIL),
                        ~Q(case_emails__status=CaseEmail.Status.DRAFT),
                    ),
                    distinct=True,
                ),
                application_update_count=Count(
                    "update_requests",
                    filter=Q(
                        update_requests__status__in=[
                            UpdateRequest.Status.CLOSED,
                            UpdateRequest.Status.RESPONDED,
                        ]
                    ),
                    distinct=True,
                ),
                fir_count=Count(
                    "further_information_requests",
                    filter=Q(
                        further_information_requests__status__in=[
                            FurtherInformationRequest.CLOSED,
                            FurtherInformationRequest.RESPONDED,
                        ]
                    ),
                    distinct=True,
                ),
                is_manufacturer_count=Count(
                    "certificateoffreesaleapplication__schedules",
                    filter=Q(
                        certificateoffreesaleapplication__schedules__exporter_status=CFSSchedule.ExporterStatus.IS_MANUFACTURER
                    ),
                    distinct=True,
                ),
                is_responsible_person_count=Count(
                    "certificateoffreesaleapplication__schedules",
                    filter=Q(
                        certificateoffreesaleapplication__schedules__schedule_statements_is_responsible_person=True
                    ),
                    distinct=True,
                ),
                countries_of_manufacture=ArrayAgg(
                    "certificateoffreesaleapplication__schedules__country_of_manufacture__name",
                    distinct=True,
                    default=Value([]),
                ),
            )
            .values(
                json=JSONObject(
                    submitted_datetime="submit_datetime",
                    application_type="application_type__type",
                    contact_title="contact__title",
                    contact_first_name="contact__first_name",
                    contact_last_name="contact__last_name",
                    agent="agent__name",
                    exporter="exporter__name",
                    process_type="process_type",
                    hse_email_count="hse_email_count",
                    beis_email_count="beis_email_count",
                    application_update_count="application_update_count",
                    fir_count="fir_count",
                    is_manufacturer_count="is_manufacturer_count",
                    is_responsible_person_count="is_responsible_person_count",
                    countries_of_manufacture="countries_of_manufacture",
                ),
            )
        )

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
            legislations=Subquery(legislation_sub_query),
            export_application=ArraySubquery(self.get_export_application_query()),
        ).values(
            "legislations",
            "export_application",
            country=F("reference_data__country__name"),
            continent=F("reference_data__country__overseas_region__name"),
            certificate_reference=F("reference"),
            case_reference=F("export_application_certificates__case_reference"),
            issue_datetime=F("export_application_certificates__case_completion_datetime"),
        )
        if self.filters.legislation:
            queryset = queryset.filter(legislations__contains=self.filters.legislation)
        return queryset.order_by("-reference")

    def serialize_row(self, cdr: dict) -> IssuedCertificateReportSerializer:
        export_application: dict = cdr["export_application"][0]
        export_application["countries_of_manufacture"] = ", ".join(
            filter(None, export_application["countries_of_manufacture"])
        )
        export_application["contact_full_name"] = utils.format_contact_name(
            export_application["contact_title"],
            export_application["contact_first_name"],
            export_application["contact_last_name"],
        )
        export_application["submitted_datetime"] = dt.datetime.fromisoformat(
            export_application["submitted_datetime"]
        )
        is_cfs = export_application.pop("process_type") == ProcessTypes.CFS

        processing_time = self.get_total_processing_time(
            cdr["issue_datetime"], export_application["submitted_datetime"]
        )
        return IssuedCertificateReportSerializer(
            is_manufacturer=(
                ""
                if not is_cfs
                else self.get_is_manufacturer(export_application["is_manufacturer_count"]).title()
            ),
            responsible_person_statement=(
                ""
                if not is_cfs
                else self.get_is_responsible_person(
                    export_application["is_responsible_person_count"]
                ).title()
            ),
            product_legislation=(
                ""
                if not is_cfs
                else ", ".join([self.legislations[pk] for pk in cdr["legislations"]])
            ),
            case_processing_time=processing_time,
            total_processing_time=processing_time,
            business_days_to_process=self.get_business_days_to_process(
                cdr["issue_datetime"],
                export_application["submitted_datetime"],
            ),
            **cdr,
            **export_application,
        )

    def get_is_responsible_person(self, is_responsible_person_count: int) -> YesNoChoices:
        return YesNoChoices.yes if is_responsible_person_count > 0 else YesNoChoices.no

    def get_is_manufacturer(self, is_manufacturer_count: int) -> YesNoChoices:
        return YesNoChoices.yes if is_manufacturer_count > 0 else YesNoChoices.no

    def get_total_processing_time(
        self, issue_datetime: dt.datetime, submit_datetime: dt.datetime
    ) -> str:
        return utils.format_time_delta(issue_datetime, submit_datetime)

    def get_business_days_to_process(
        self, end_datetime: dt.datetime, start_datetime: dt.datetime
    ) -> int:
        start_date = start_datetime.date()
        end_date = end_datetime.date()
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
            .annotate(
                ima_type=F("application_type__type"),
                ima_sub_type=F("application_type__sub_type"),
                agent_name=F("agent__name"),
                country_of_origin=F("origin_country__name"),
                country_of_consignment=F("consignment_country__name"),
                wood_shipping_year=F("woodquotaapplication__shipping_year"),
                iron_shipping_year=F("ironsteelapplication__shipping_year"),
                com_group_name=F("commodity_group__group_name"),
                importer_printable=F("application_type__importer_printable"),
                commodity_code=F("priorsurveillanceapplication__commodity__commodity_code"),
                contact_title=F("contact__title"),
                contact_first_name=F("contact__first_name"),
                contact_last_name=F("contact__last_name"),
            )
            .order_by("-reference")
            .distinct()
            .select_related("importer")
            .prefetch_related("licences")
        )
        if self.filters.application_type:
            queryset = queryset.filter(application_type__type=self.filters.application_type)
        return queryset

    def serialize_row(self, import_application: ImportApplication) -> ImportLicenceSerializer:
        ia = import_application
        is_adhoc = import_application.process_type == ProcessTypes.SANCTIONS
        is_sps = import_application.process_type == ProcessTypes.SPS
        licence = utils.get_licence_details(ia)
        contact_full_name = utils.format_contact_name(
            ia.contact_title, ia.contact_first_name, ia.contact_last_name
        )
        return self.ReportSerializer(
            case_reference=ia.get_reference(),
            licence_reference=licence.reference,
            licence_type=licence.licence_type,
            under_appeal="",  # Unused field in V1
            ima_type=ia.ima_type,
            ima_type_title=self.get_ima_type_title(ia.ima_type),
            ima_sub_type=ia.ima_sub_type,
            ima_sub_type_title=self.get_ima_sub_type_title(ia.ima_sub_type),
            variation_number=utils.get_variation_number(ia.reference),
            status=ia.status,
            importer=ia.importer.display_name,
            agent_name=ia.agent_name,
            app_contact_name=contact_full_name,
            country_of_origin=ia.country_of_origin,
            country_of_consignment=ia.country_of_consignment,
            shipping_year=ia.wood_shipping_year or ia.iron_shipping_year or "",
            com_group_name=ia.com_group_name,
            commodity_codes=self.get_commodity_codes(import_application, is_adhoc, is_sps),
            initial_submitted_datetime=ia.submit_datetime,
            initial_case_closed_datetime=licence.initial_case_closed_datetime,
            time_to_initial_close=licence.time_to_initial_close,
            latest_case_closed_datetime=licence.latest_case_closed_datetime,
            licence_dates=utils.get_licence_dates(licence),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            importer_printable=ia.importer_printable,
        )

    def get_ima_sub_type_title(self, ima_sub_type: str) -> str:
        try:
            return ImportApplicationType.SubTypes(ima_sub_type).label
        except ValueError:
            return ima_sub_type

    def get_ima_type_title(self, ima_type: str) -> str:
        try:
            return ImportApplicationType.Types(ima_type).label
        except ValueError:
            return ima_type

    def get_commodity_codes(
        self, import_application: ImportApplication, is_adhoc: bool, is_sps: bool
    ) -> str:
        if is_sps and import_application.commodity_code:
            return f"Code: {import_application.commodity_code}"

        if not is_adhoc:
            return ""

        details = []
        ia = import_application.get_specific_model()
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
            .annotate(
                country_of_origin=F("origin_country__name"),
                country_of_consignment=F("consignment_country__name"),
                application_sub_type=F("application_type__sub_type"),
                endorsement_list=ArrayAgg(
                    "endorsements__content",
                    distinct=True,
                    filter=Q(endorsements__isnull=False),
                    default=Value([]),
                ),
            )
            .order_by("-reference")
            .select_related("importer", "importer_office")
            .prefetch_related("licences")
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
                results.append(self.serialize_row(report_firearms, import_application))
        return results

    def serialize_row(
        self, s: ReportFirearms, ia: ImportApplication
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
            case_type=ia.application_sub_type,
            importer=ia.importer.display_name,
            eori_number=ia.importer.eori_number,
            importer_address=utils.get_importer_address(ia),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            country_of_origin=ia.country_of_origin,
            country_of_consignment=ia.country_of_consignment,
            endorsements="\n".join(ia.endorsement_list),
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
