import datetime as dt
import json
from collections.abc import Callable
from functools import wraps
from itertools import chain
from typing import Any, ClassVar, final

from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import (
    Count,
    F,
    FilteredRelation,
    Max,
    Min,
    Model,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.functions import JSONObject
from pydantic import BaseModel, ConfigDict, SerializeAsAny, ValidationError

from web.domains.case._import.fa.types import FaImportApplication, ReportFirearms
from web.domains.case._import.fa_sil.types import GoodsModel
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpAccessOrExpAccess
from web.domains.user.utils import user_list_view_qs
from web.flow.models import ProcessTypes
from web.mail.constants import CaseEmailCodes
from web.models import SILGoodsSection582Obsolete  # /PS-IGNORE
from web.models import SILGoodsSection582Other  # /PS-IGNORE
from web.models import SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
from web.models import SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE
from web.models import (
    AccessRequest,
    CaseDocumentReference,
    CaseEmail,
    CFSSchedule,
    DFLSupplementaryReportFirearm,
    EndorsementImportApplication,
    ExportApplication,
    ExportApplicationCertificate,
    ExporterAccessRequest,
    ExporterUserObjectPermission,
    FurtherInformationRequest,
    ImportApplication,
    ImportApplicationType,
    ImporterAccessRequest,
    ImporterUserObjectPermission,
    OILSupplementaryReportFirearm,
    OpenIndividualLicenceApplication,
    ProductLegislation,
    SanctionsAndAdhocApplicationGoods,
    ScheduleReport,
    SILGoodsSection1,
    SILGoodsSection2,
    SILGoodsSection5,
    SILLegacyGoods,
    SILSupplementaryReportFirearmSection1,
    SILSupplementaryReportFirearmSection2,
    SILSupplementaryReportFirearmSection5,
    SILSupplementaryReportFirearmSectionLegacy,
    UpdateRequest,
    User,
    UserImportCertificate,
)
from web.permissions import Perms, StaffUserGroups
from web.utils.pdf.utils import get_fa_sil_goods_item
from web.utils.search.app_data import _add_import_licence_data
from web.utils.sentry import capture_exception

from . import utils
from .constants import NO, YES, DateFilterType, UserDateFilterType
from .serializers import (
    AccessRequestTotalsReportSerializer,
    DFLFirearmsLicenceSerializer,
    ErrorSerializer,
    ExporterAccessRequestReportSerializer,
    GoodsSectionSerializer,
    ImporterAccessRequestReportSerializer,
    ImportLicenceSerializer,
    IssuedCertificateReportSerializer,
    OILFirearmsLicenceSerializer,
    SILFirearmsLicenceSerializer,
    StaffUserSerializer,
    SupplementaryFirearmsSerializer,
    UserSerializer,
)


def handle_error(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> list:
        try:
            return f(self, *args, **kwargs)
        except ValidationError as e:
            for error_dict in json.loads(e.json()):
                self.errors.append(
                    ErrorSerializer(
                        report_name=self.name,
                        identifier=self.get_row_identifier(*args, **kwargs),
                        error_type="Validation Error",
                        error_message=error_dict["msg"],
                        column=", ".join(error_dict["loc"]),
                        value=error_dict["input"],
                    )
                )
        except Exception as e:
            capture_exception()
            self.errors.append(
                ErrorSerializer(
                    report_name=self.name,
                    identifier=self.get_row_identifier(*args, **kwargs),
                    error_type=type(e).__name__,
                    error_message="",
                    column="",
                    value="",
                )
            )
        return []

    return wrapper


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


class UserFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date_filter_type: UserDateFilterType
    date_from: str
    date_to: str


class BasicReportFilter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date_from: str
    date_to: str


class ReportResults(BaseModel):
    results: list[SerializeAsAny[BaseModel]]
    header: list[str]
    errors: list[ErrorSerializer]


class ReportInterface:
    """The reporting interface all reports must subclass."""

    ReportFilter: ClassVar[type[BaseModel]]
    ReportSerializer: ClassVar[type[BaseModel]]
    name: ClassVar[str]

    def __init__(self, scheduled_report: ScheduleReport) -> None:
        self.scheduled_report = scheduled_report
        self.filters = self.ReportFilter(**self.scheduled_report.parameters)
        self.errors: list[ErrorSerializer] = []

    def get_data(self) -> dict[str, Any]:
        return ReportResults(
            results=self.process_results(),
            header=self.get_header(),
            errors=self.errors,
        ).model_dump(by_alias=True)

    def process_results(self) -> list[BaseModel]:
        results = []
        for r in self.get_queryset().iterator(500):
            results += self.serialize_rows(r)
        return list(filter(None, results))

    def get_header(self) -> list[str]:
        schema = self.ReportSerializer.model_json_schema(by_alias=True, mode="serialization")
        return schema["required"]

    @handle_error
    def serialize_rows(self, r: Model | dict) -> list:
        """r can either be a model or a dict.

        When get_queryset returned a queryset r is a Model instance.
        When get_queryset returns queryset.values() r is a dict.
        """

        return [self.serialize_row(r)]

    def serialize_row(self, *args: Any, **kwargs: Any) -> BaseModel:
        raise NotImplementedError

    def get_queryset(self) -> QuerySet:
        raise NotImplementedError

    def add_licence_data_query(self, queryset: QuerySet) -> QuerySet:
        queryset = _add_import_licence_data(queryset, distinct=False)
        return queryset.annotate(
            initial_case_closed_datetime=Min("valid_licences__case_completion_datetime")
        )

    def get_sil_section_query(
        self,
        model: type[GoodsModel],
        obsolete_calibre: bool = True,
        unlimited_quantity: bool = True,
    ) -> QuerySet:
        extra_fields: dict[str, str] = {}
        if obsolete_calibre:
            extra_fields = extra_fields | {"obsolete_calibre": "obsolete_calibre"}
        if unlimited_quantity:
            extra_fields = extra_fields | {"unlimited_quantity": "unlimited_quantity"}

        if model == SILGoodsSection5:
            extra_fields["clause"] = "section_5_clause__clause"

        return (
            model.objects.filter(Q(import_application_id=OuterRef("pk")))
            .filter(is_active=True)
            .values(json=JSONObject(description="description", quantity="quantity", **extra_fields))
        )

    def get_report_query(
        self,
        model: type[ReportFirearms],
        process_type: ProcessTypes,
        quantity_unlimited: bool = False,
    ) -> QuerySet:
        extra_fields: dict[str, str] = {}
        if process_type == ProcessTypes.FA_DFL:
            extra_fields = extra_fields | {"description": "goods_certificate__goods_description"}
        elif process_type != ProcessTypes.FA_OIL:
            extra_fields = extra_fields | {
                "description": "goods_certificate__description",
                "goods_certificate_quantity": "goods_certificate__quantity",
            }
        if quantity_unlimited:
            extra_fields = extra_fields | {
                "goods_certificate_unlimited": "goods_certificate__unlimited_quantity",
            }
        return (
            model.objects.filter(
                report__supplementary_info__import_application_id=OuterRef("pk"),
            )
            .filter(Q(is_manual=True) | Q(is_upload=True) | Q(is_no_firearm=True))
            .values(
                json=JSONObject(
                    make_model="model",
                    frame_serial_number="serial_number",
                    calibre="calibre",
                    proofing="proofing",
                    document="document",
                    means_of_transport="report__transport",
                    date_firearms_received="report__date_received",
                    bought_from_reg_no="report__bought_from__registration_number",
                    bought_from_first_name="report__bought_from__first_name",
                    bought_from_last_name="report__bought_from__last_name",
                    bought_from_street="report__bought_from__street",
                    bought_from_city="report__bought_from__city",
                    bought_from_postcode="report__bought_from__postcode",
                    bought_from_region="report__bought_from__region",
                    bought_from_country="report__bought_from__country__name",
                    all_reported="report__supplementary_info__is_complete",
                    **extra_fields,
                )
            )
        )

    def get_row_identifier(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError


class BaseFirearmsLicenceInterface(ReportInterface):
    ReportFilter = BasicReportFilter
    filters: BasicReportFilter

    def get_application_filter(self) -> Q:
        raise NotImplementedError

    def get_constabularies(self) -> QuerySet:
        return UserImportCertificate.objects.filter(
            Q(oil_application__id=OuterRef("pk")) | Q(sil_application__id=OuterRef("pk"))
        ).values("constabulary__name")

    def get_endorsements_query(self) -> QuerySet:
        return (
            EndorsementImportApplication.objects.filter(import_application_id=OuterRef("pk"))
            .values("content")
            .distinct("content")
        )

    def get_queryset(self) -> QuerySet:
        _filter = Q(
            licences__case_completion_datetime__date__range=(
                self.filters.date_from,
                self.filters.date_to,
            )
        )
        queryset = (
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
                endorsement_list=ArraySubquery(self.get_endorsements_query()),
                dfl_constabulary=F("dflapplication__constabulary__name"),
                constabularies_list=ArraySubquery(self.get_constabularies()),
                importer_eori_number=F("importer__eori_number"),
                importer_title=F("importer__user__title"),
                importer_first_name=F("importer__user__first_name"),
                importer_last_name=F("importer__user__last_name"),
                organisation_name=F("importer__name"),
                importer_address_1=F("importer_office__address_1"),
                importer_address_2=F("importer_office__address_2"),
                importer_address_3=F("importer_office__address_3"),
                importer_address_4=F("importer_office__address_4"),
                importer_address_5=F("importer_office__address_5"),
                importer_address_6=F("importer_office__address_6"),
                importer_address_7=F("importer_office__address_7"),
                importer_address_8=F("importer_office__address_8"),
                importer_postcode=F("importer_office__postcode"),
                constabulary_emails=FilteredRelation(
                    "case_emails",
                    condition=Q(
                        Q(case_emails__template_code=CaseEmailCodes.CONSTABULARY_CASE_EMAIL),
                        ~Q(case_emails__status=CaseEmail.Status.DRAFT),
                    ),
                ),
                constabulary_email_first_email_sent=Min(F("constabulary_emails__sent_datetime")),
                constabulary_email_last_email_closed=Max(F("constabulary_emails__closed_datetime")),
                dfl_certificate_descriptions=ArrayAgg(
                    "dflapplication__goods_certificates__goods_description",
                    distinct=True,
                    default=Value([]),
                ),
                section_1=ArraySubquery(
                    self.get_sil_section_query(SILGoodsSection1, obsolete_calibre=False)
                ),
                section_2=ArraySubquery(
                    self.get_sil_section_query(SILGoodsSection2, obsolete_calibre=False)
                ),
                section_5=ArraySubquery(
                    self.get_sil_section_query(SILGoodsSection5, obsolete_calibre=False)
                ),
                section_legacy=ArraySubquery(self.get_sil_section_query(SILLegacyGoods)),
                section_other=ArraySubquery(
                    self.get_sil_section_query(
                        SILGoodsSection582Other,  # /PS-IGNORE
                        obsolete_calibre=False,
                        unlimited_quantity=False,
                    )
                ),
                section_obsolete=ArraySubquery(
                    self.get_sil_section_query(
                        SILGoodsSection582Obsolete,  # /PS-IGNORE
                        unlimited_quantity=False,
                    ),
                ),
            )
            .order_by("reference")
        )
        queryset = self.add_licence_data_query(queryset)
        return queryset.values(
            "country_of_origin",
            "country_of_consignment",
            "reference",
            "status",
            "submit_datetime",
            "last_submit_datetime",
            "endorsement_list",
            "application_sub_type",
            "dfl_constabulary",
            "constabularies_list",
            "latest_licence_start_date",
            "latest_licence_end_date",
            "latest_licence_issue_paper_licence_only",
            "latest_licence_status",
            "latest_licence_cdr_data",
            "latest_licence_case_completion_datetime",
            "initial_case_closed_datetime",
            "importer_eori_number",
            "importer_title",
            "importer_first_name",
            "importer_last_name",
            "organisation_name",
            "importer_address_1",
            "importer_address_2",
            "importer_address_3",
            "importer_address_4",
            "importer_address_5",
            "importer_address_6",
            "importer_address_7",
            "importer_address_8",
            "importer_postcode",
            "constabulary_email_first_email_sent",
            "constabulary_email_last_email_closed",
            "dfl_certificate_descriptions",
            "section_1",
            "section_2",
            "section_5",
            "section_legacy",
            "section_other",
            "section_obsolete",
        )

    def serialize_row(self, ia: dict) -> BaseModel:
        licence = utils.get_licence_details(ia)
        import_user_name = utils.format_contact_name(
            ia["importer_title"], ia["importer_first_name"], ia["importer_last_name"]
        )

        return self.ReportSerializer(
            licence_reference=licence.reference,
            variation_number=utils.get_variation_number(ia["reference"]),
            case_reference=ia["reference"],
            importer=ia["organisation_name"] or import_user_name,
            eori_number=ia["importer_eori_number"],
            importer_address=utils.format_importer_address(ia),
            first_submitted_date=ia["submit_datetime"].date(),
            final_submitted_date=ia["last_submit_datetime"].date(),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            endorsements="\n".join(ia["endorsement_list"]),
            revoked=ia["status"] == ImportApplication.Statuses.REVOKED,
            **self.extra_fields(ia),
            **ia,
        )

    def get_row_identifier(self, ia: ImportApplication) -> str:
        return ia["reference"]

    def extra_fields(self, ia: dict) -> dict[str, Any]:
        raise NotImplementedError


@final
class IssuedCertificateReportInterface(ReportInterface):
    ReportSerializer = IssuedCertificateReportSerializer
    ReportFilter = IssuedCertificateReportFilter
    name = "Issued Certificates"

    # Added to fix typing
    filters: IssuedCertificateReportFilter

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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
                        Q(case_emails__template_code=CaseEmailCodes.HSE_CASE_EMAIL),
                        ~Q(case_emails__status=CaseEmail.Status.DRAFT),
                    ),
                    distinct=True,
                ),
                beis_email_count=Count(
                    "case_emails",
                    filter=Q(
                        Q(case_emails__template_code=CaseEmailCodes.BEIS_CASE_EMAIL),
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
                "" if not is_cfs else YES if export_application["is_manufacturer_count"] > 0 else NO
            ),
            responsible_person_statement=(
                ""
                if not is_cfs
                else YES if export_application["is_responsible_person_count"] > 0 else NO
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

    def get_row_identifier(self, cdr: CaseDocumentReference) -> str:
        return cdr["case_reference"]

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

    def get_row_identifier(self, ar: ImpAccessOrExpAccess) -> str:
        return ar.reference


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

    @handle_error
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

    def get_row_identifier(self, **kwargs: Any) -> str:
        return "Totals"


@final
class ImportLicenceInterface(ReportInterface):
    name = "Import Licence Data Extract"
    ReportSerializer = ImportLicenceSerializer
    ReportFilter = ImportLicenceFilter
    filters: ImportLicenceFilter

    def get_sanctions_goods_query(self) -> QuerySet:
        return (
            SanctionsAndAdhocApplicationGoods.objects.filter(import_application_id=OuterRef("pk"))
            .values(
                json=JSONObject(
                    commodity_code="commodity__commodity_code",
                    goods_description="goods_description",
                )
            )
            .order_by("-commodity")
        )

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
                sanctions_commodities=ArraySubquery(self.get_sanctions_goods_query()),
                organisation_name=F("importer__name"),
                importer_title=F("importer__user__title"),
                importer_first_name=F("importer__user__first_name"),
                importer_last_name=F("importer__user__last_name"),
            )
            .order_by("-reference")
            .distinct()
        )
        if self.filters.application_type:
            queryset = queryset.filter(application_type__type=self.filters.application_type)
        queryset = self.add_licence_data_query(queryset)
        return queryset.values(
            "pk",
            "country_of_origin",
            "country_of_consignment",
            "reference",
            "status",
            "submit_datetime",
            "latest_licence_start_date",
            "latest_licence_end_date",
            "latest_licence_issue_paper_licence_only",
            "latest_licence_status",
            "latest_licence_cdr_data",
            "latest_licence_case_completion_datetime",
            "initial_case_closed_datetime",
            "ima_type",
            "ima_sub_type",
            "organisation_name",
            "importer_title",
            "importer_first_name",
            "importer_last_name",
            "contact_title",
            "contact_first_name",
            "contact_last_name",
            "importer_printable",
            "iron_shipping_year",
            "wood_shipping_year",
            "agent_name",
            "com_group_name",
            "sanctions_commodities",
            "commodity_code",
        )

    def get_row_identifier(self, ia: ImportApplication) -> str:
        return ia["reference"]

    def serialize_row(self, ia: dict) -> ImportLicenceSerializer:
        licence = utils.get_licence_details(ia)
        import_user_name = utils.format_contact_name(
            ia["importer_title"], ia["importer_first_name"], ia["importer_last_name"]
        )

        contact_full_name = utils.format_contact_name(
            ia["contact_title"], ia["contact_first_name"], ia["contact_last_name"]
        )
        return self.ReportSerializer(
            case_reference=ia["reference"],
            licence_reference=licence.reference,
            licence_type=licence.licence_type,
            under_appeal="",  # Unused field in V1
            ima_type=ia["ima_type"],
            ima_type_title=self.get_ima_type_title(ia["ima_type"]),
            ima_sub_type=ia["ima_sub_type"],
            ima_sub_type_title=self.get_ima_sub_type_title(ia["ima_sub_type"]),
            variation_number=utils.get_variation_number(ia["reference"]),
            status=ia["status"],
            importer=ia["organisation_name"] or import_user_name,
            agent_name=ia["agent_name"],
            app_contact_name=contact_full_name,
            country_of_origin=ia["country_of_origin"],
            country_of_consignment=ia["country_of_consignment"],
            shipping_year=ia["wood_shipping_year"] or ia["iron_shipping_year"] or "",
            com_group_name=ia["com_group_name"],
            commodity_codes=self.get_commodity_codes(ia),
            initial_submitted_datetime=ia["submit_datetime"],
            initial_case_closed_datetime=licence.initial_case_closed_datetime,
            time_to_initial_close=licence.time_to_initial_close,
            latest_case_closed_datetime=licence.latest_case_closed_datetime,
            licence_dates=utils.get_licence_dates(licence),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            importer_printable=ia["importer_printable"],
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

    def get_commodity_codes(self, ia: dict) -> str:
        commodity_code = ia["commodity_code"]
        if commodity_code:
            return f"Code: {commodity_code}"

        details = []
        for goods in ia["sanctions_commodities"]:
            details.append(f"Code: {goods['commodity_code']}; Desc: {goods['goods_description']}")
        return ", ".join(details)


@final
class SupplementaryFirearmsInterface(ReportInterface):
    name = "Supplementary firearms report"
    ReportSerializer = SupplementaryFirearmsSerializer
    ReportFilter = BasicReportFilter
    filters: BasicReportFilter

    def get_endorsements_query(self) -> QuerySet:
        return (
            EndorsementImportApplication.objects.filter(import_application_id=OuterRef("pk"))
            .values("content")
            .distinct("content")
        )

    def get_constabularies(self) -> QuerySet:
        return UserImportCertificate.objects.filter(
            Q(oil_application__id=OuterRef("pk")) | Q(sil_application__id=OuterRef("pk"))
        ).values("constabulary__name")

    def get_queryset(self) -> QuerySet:
        _filter = Q(
            licences__case_completion_datetime__date__range=(
                self.filters.date_from,
                self.filters.date_to,
            )
        )
        queryset = (
            ImportApplication.objects.filter(
                _filter,
                Q(silapplication__supplementary_info__isnull=False)
                | Q(openindividuallicenceapplication__supplementary_info__isnull=False)
                | Q(dflapplication__supplementary_info__isnull=False),
            )
            .exclude(status__in=[ImpExpStatus.IN_PROGRESS, ImpExpStatus.DELETED])
            .annotate(
                organisation_name=F("importer__name"),
                country_of_origin=F("origin_country__name"),
                country_of_consignment=F("consignment_country__name"),
                application_sub_type=F("application_type__sub_type"),
                dfl_constabulary=F("dflapplication__constabulary__name"),
                importer_eori_number=F("importer__eori_number"),
                constabularies_list=ArraySubquery(self.get_constabularies()),
                endorsement_list=ArraySubquery(self.get_endorsements_query()),
                section_1_reports=ArraySubquery(
                    self.get_report_query(
                        SILSupplementaryReportFirearmSection1, ProcessTypes.FA_SIL
                    )
                ),
                section_2_reports=ArraySubquery(
                    self.get_report_query(
                        SILSupplementaryReportFirearmSection2, ProcessTypes.FA_SIL
                    )
                ),
                section_5_reports=ArraySubquery(
                    self.get_report_query(
                        SILSupplementaryReportFirearmSection5, ProcessTypes.FA_SIL
                    )
                ),
                section_582_reports=ArraySubquery(
                    self.get_report_query(
                        SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
                        ProcessTypes.FA_SIL,
                        quantity_unlimited=False,
                    )
                ),
                section_5_obsolete_reports=ArraySubquery(
                    self.get_report_query(
                        SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
                        ProcessTypes.FA_SIL,
                        quantity_unlimited=False,
                    )
                ),
                section_legacy_reports=ArraySubquery(
                    self.get_report_query(
                        SILSupplementaryReportFirearmSectionLegacy, ProcessTypes.FA_SIL
                    )
                ),
                oil_reports=ArraySubquery(
                    self.get_report_query(OILSupplementaryReportFirearm, ProcessTypes.FA_OIL),
                ),
                dfl_reports=ArraySubquery(
                    self.get_report_query(DFLSupplementaryReportFirearm, ProcessTypes.FA_DFL),
                ),
                importer_title=F("importer__user__title"),
                importer_first_name=F("importer__user__first_name"),
                importer_last_name=F("importer__user__last_name"),
                importer_address_1=F("importer_office__address_1"),
                importer_address_2=F("importer_office__address_2"),
                importer_address_3=F("importer_office__address_3"),
                importer_address_4=F("importer_office__address_4"),
                importer_address_5=F("importer_office__address_5"),
                importer_address_6=F("importer_office__address_6"),
                importer_address_7=F("importer_office__address_7"),
                importer_address_8=F("importer_office__address_8"),
                importer_postcode=F("importer_office__postcode"),
            )
            .order_by("-reference")
        )
        queryset = self.add_licence_data_query(queryset)
        return queryset.values(
            "section_1_reports",
            "section_2_reports",
            "section_5_reports",
            "section_5_obsolete_reports",
            "section_legacy_reports",
            "section_582_reports",
            "oil_reports",
            "dfl_reports",
            "latest_licence_start_date",
            "latest_licence_end_date",
            "latest_licence_issue_paper_licence_only",
            "latest_licence_status",
            "latest_licence_cdr_data",
            "latest_licence_case_completion_datetime",
            "initial_case_closed_datetime",
            "process_type",
            "application_sub_type",
            "organisation_name",
            "importer_eori_number",
            "country_of_origin",
            "country_of_consignment",
            "endorsement_list",
            "importer_title",
            "importer_first_name",
            "importer_last_name",
            "submit_datetime",
            "reference",
            "importer_address_1",
            "importer_address_2",
            "importer_address_3",
            "importer_address_4",
            "importer_address_5",
            "importer_address_6",
            "importer_address_7",
            "importer_address_8",
            "importer_postcode",
            "dfl_constabulary",
            "constabularies_list",
        )

    def serialize_rows(self, ia: dict) -> list:
        results = []
        for report_firearms in chain(
            ia["section_1_reports"],
            ia["section_2_reports"],
            ia["section_5_reports"],
            ia["section_5_obsolete_reports"],
            ia["section_legacy_reports"],
            ia["section_582_reports"],
            ia["oil_reports"],
            ia["dfl_reports"],
        ):
            results.append(self.serialize_row(report_firearms, ia))
        return results

    def get_row_identifier(self, s: ReportFirearms, ia: FaImportApplication) -> str:
        return ia["reference"]

    @handle_error
    def serialize_row(self, s: ReportFirearms, ia: dict) -> SupplementaryFirearmsSerializer:
        is_dfl = ia["process_type"] == ProcessTypes.FA_DFL
        is_sil = ia["process_type"] == ProcessTypes.FA_SIL
        is_oil = ia["process_type"] == ProcessTypes.FA_OIL
        import_user_name = utils.format_contact_name(
            ia["importer_title"], ia["importer_first_name"], ia["importer_last_name"]
        )

        licence = utils.get_licence_details(ia)

        if s["bought_from_first_name"]:
            bought_from_name = (
                f"{s['bought_from_first_name']} {s['bought_from_first_name']}"
                if s["bought_from_last_name"]
                else s["bought_from_first_name"]
            )
            bought_from_reg_no = s["bought_from_reg_no"]
            bought_from_address = ", ".join(
                filter(
                    None,
                    [
                        s["bought_from_street"],
                        s["bought_from_city"],
                        s["bought_from_postcode"],
                        s["bought_from_region"],
                        s["bought_from_country"],
                    ],
                )
            )
        else:
            bought_from_name = ""
            bought_from_reg_no = ""
            bought_from_address = ""

        goods_quantity = s.get("goods_certificate_quantity") or (1 if is_dfl else 0)
        exceed_quantity = is_sil and s.get("goods_certificate_unlimited", False)
        description = (
            OpenIndividualLicenceApplication.goods_description() if is_oil else s["description"]
        )
        constabularies = ia["dfl_constabulary"] if is_dfl else ", ".join(ia["constabularies_list"])

        return self.ReportSerializer(
            licence_reference=licence.reference,
            case_reference=ia["reference"],
            case_type=ia["application_sub_type"],
            importer=ia["organisation_name"] or import_user_name,
            eori_number=ia["importer_eori_number"],
            importer_address=utils.format_importer_address(ia),
            licence_start_date=licence.start_date,
            licence_expiry_date=licence.end_date,
            country_of_origin=ia["country_of_origin"],
            country_of_consignment=ia["country_of_consignment"],
            endorsements="\n".join(ia["endorsement_list"]),
            report_date=s["date_firearms_received"],
            constabularies=constabularies,
            who_bought_from_name=bought_from_name,
            who_bought_from_reg_no=bought_from_reg_no,
            who_bought_from_address=bought_from_address,
            frame_serial_number=s["frame_serial_number"],
            means_of_transport=s["means_of_transport"],
            date_firearms_received=s["date_firearms_received"],
            calibre=s["calibre"],
            proofing=s["proofing"].title() if s["proofing"] else "",
            make_model=s["make_model"],
            firearms_document="See uploaded files on report" if s["document"] else "",
            all_reported=s["all_reported"],
            goods_description=description,
            goods_quantity=goods_quantity,
            firearms_exceed_quantity=exceed_quantity,
            goods_description_with_subsection=description,
        )


@final
class DFLFirearmsLicenceInterface(BaseFirearmsLicenceInterface):
    name = "Deactivated Firearms Licences"
    ReportSerializer = DFLFirearmsLicenceSerializer

    def get_application_filter(self) -> Q:
        return Q(dflapplication__isnull=False)

    def extra_fields(self, ia: dict) -> dict[str, Any]:
        return {"goods_description": "\n".join(ia["dfl_certificate_descriptions"])}


@final
class OILFirearmsLicenceInterface(BaseFirearmsLicenceInterface):
    name = "Open Firearms Licences"
    ReportSerializer = OILFirearmsLicenceSerializer

    def get_application_filter(self) -> Q:
        return Q(openindividuallicenceapplication__isnull=False)

    def extra_fields(self, ia: dict) -> dict[str, Any]:
        constabulary_email_times = utils.get_constabulary_email_times(ia)
        return {
            "constabularies": ", ".join(ia["constabularies_list"]),
            "first_constabulary_email_sent_date": constabulary_email_times.first_email_sent,
            "last_constabulary_email_closed_date": constabulary_email_times.last_email_closed,
        }


@final
class SILFirearmsLicenceInterface(BaseFirearmsLicenceInterface):
    name = "Specific Firearms Licences"
    ReportSerializer = SILFirearmsLicenceSerializer

    def get_application_filter(self) -> Q:
        return Q(silapplication__isnull=False)

    def extra_fields(self, ia: dict) -> dict[str, Any]:
        constabulary_email_times = utils.get_constabulary_email_times(ia)

        descriptions = []
        for (
            goods_section,
            sections,
        ) in [
            ("goods_section1", ia["section_1"]),
            ("goods_section2", ia["section_2"]),
            ("goods_section5", ia["section_5"]),
            ("goods_legacy", ia["section_legacy"]),
            ("goods_section582_others", ia["section_other"]),
            ("goods_section582_obsoletes", ia["section_obsolete"]),
        ]:
            items = get_fa_sil_goods_item(
                goods_section, (GoodsSectionSerializer(**r) for r in sections)
            )
            descriptions.extend([f"{quantity} x {desc}" for desc, quantity in items])

        return {
            "constabularies": ", ".join(ia["constabularies_list"]),
            "goods_description": "\n".join(descriptions),
            "first_constabulary_email_sent_date": constabulary_email_times.first_email_sent,
            "last_constabulary_email_closed_date": constabulary_email_times.last_email_closed,
        }


class ActiveUserInterface(ReportInterface):
    name = "Active Users"
    ReportSerializer = UserSerializer
    ReportFilter = UserFilter
    filters: UserFilter

    def get_permission_filter(self) -> Q:
        return Q(
            groups__permissions__codename__in=[
                Perms.sys.exporter_access.codename,
                Perms.sys.importer_access.codename,
            ]
        )

    def get_queryset(self) -> QuerySet:
        if self.filters.date_filter_type == UserDateFilterType.LAST_LOGIN:
            _filter = Q(
                last_login__date__range=(
                    self.filters.date_from,
                    self.filters.date_to,
                )
            )
        else:
            _filter = Q(
                date_joined__date__range=(
                    self.filters.date_from,
                    self.filters.date_to,
                )
            )

        return (
            user_list_view_qs()
            .filter(_filter, self.get_permission_filter(), is_active=True)
            .exclude(groups__name__in=StaffUserGroups)
            .annotate(
                exporters=ArraySubquery(
                    ExporterUserObjectPermission.objects.filter(user__pk=OuterRef("pk"))
                    .values_list("content_object__name", flat=True)
                    .distinct()
                ),
                importers=ArraySubquery(
                    ImporterUserObjectPermission.objects.filter(user__pk=OuterRef("pk"))
                    .values_list("content_object__name", flat=True)
                    .distinct()
                ),
                primary_email=FilteredRelation("emails", condition=Q(emails__is_primary=True)),
                primary_email_address=F("primary_email__email"),
                date_joined_date=F("date_joined__date"),
                last_login_date=F("last_login__date"),
            )
            .distinct()
            .values(
                "first_name",
                "last_name",
                "email",
                "primary_email_address",
                "date_joined_date",
                "last_login_date",
                "exporters",
                "importers",
            )
            .order_by("pk")
        )

    def serialize_row(self, user: dict) -> UserSerializer:
        return self.ReportSerializer(
            first_name=user["first_name"],
            last_name=user["last_name"],
            email_address=user["email"],
            primary_email_address=(
                user["primary_email_address"] if user["primary_email_address"] else user["email"]
            ),
            is_importer=True if user["importers"] else False,
            is_exporter=True if user["exporters"] else False,
            businesses=", ".join(user["exporters"] + user["importers"]),
            date_joined=user["date_joined_date"],
            last_login=user["last_login_date"],
        )

    def get_row_identifier(self, user: User) -> str:
        return user["email"]


class ActiveStaffUserInterface(ReportInterface):
    name = "Active Staff Users"
    ReportSerializer = StaffUserSerializer
    ReportFilter = UserFilter
    filters: UserFilter

    def get_queryset(self) -> QuerySet:
        if self.filters.date_filter_type == UserDateFilterType.LAST_LOGIN:
            _filter = Q(
                last_login__date__range=(
                    self.filters.date_from,
                    self.filters.date_to,
                )
            )
        else:
            _filter = Q(
                date_joined__date__range=(
                    self.filters.date_from,
                    self.filters.date_to,
                )
            )
        _permissions_filter = Q(groups__name__in=StaffUserGroups)
        return (
            user_list_view_qs()
            .filter(_filter, _permissions_filter, is_active=True)
            .annotate(
                date_joined_date=F("date_joined__date"),
                last_login_date=F("last_login__date"),
                primary_email=FilteredRelation("emails", condition=Q(emails__is_primary=True)),
                primary_email_address=F("primary_email__email"),
            )
            .distinct()
            .values(
                "first_name",
                "last_name",
                "email",
                "primary_email_address",
                "date_joined_date",
                "last_login_date",
            )
            .order_by("pk")
        )

    def serialize_row(self, user: dict) -> StaffUserSerializer:
        return self.ReportSerializer(
            first_name=user["first_name"],
            last_name=user["last_name"],
            email_address=user["email"],
            primary_email_address=(
                user["primary_email_address"] if user["primary_email_address"] else user["email"]
            ),
            date_joined=user["date_joined_date"],
            last_login=user["last_login_date"],
        )

    def get_row_identifier(self, user: User) -> str:
        return user["email"]


class RegisteredUserInterface(ActiveUserInterface):
    name = "Registered Users"

    def get_permission_filter(self) -> Q:
        return Q(groups__isnull=True)
