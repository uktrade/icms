import datetime as dt

from web.domains.case._import.fa.types import FaImportApplication
from web.domains.case.services import document_pack
from web.flow.models import ProcessTypes
from web.mail.constants import EmailTypes
from web.models import (
    CaseDocumentReference,
    ExportApplicationType,
    ImportApplication,
    ImportApplicationType,
    ProductLegislation,
    ScheduleReport,
)

from .constants import DateFilterType, ReportType
from .serializers import (
    ConstabularyEmailTimesSerializer,
    LicenceSerializer,
    format_label,
)


def get_importer_address(ia: ImportApplication) -> str:
    importer_address = ia.importer_office.address.replace("\n", ", ")
    if ia.importer_office.postcode:
        importer_address = f"{importer_address}, {ia.importer_office.postcode}"
    return importer_address


def get_licence_details(ia: ImportApplication) -> LicenceSerializer:
    packs = document_pack.pack_licence_history(ia)
    latest_pack = packs.last()
    if not latest_pack:
        return LicenceSerializer(
            reference="",
            start_date=None,
            end_date=None,
            status=None,
            licence_type="Electronic",
            latest_case_closed_datetime=None,
            initial_case_closed_datetime=None,
            time_to_initial_close="",
        )
    if packs.count() == 1:
        initial_case_completion_datetime = latest_pack.case_completion_datetime
    else:
        first_pack = packs.first()
        initial_case_completion_datetime = first_pack.case_completion_datetime

    if ia.legacy_case_flag or ia.status == ImportApplication.Statuses.WITHDRAWN:
        licence_ref = ""
    else:
        licence = latest_pack.document_references.filter(
            document_type=CaseDocumentReference.Type.LICENCE
        ).first()
        licence_ref = licence.reference

    time_to_initial_close = format_time_delta(
        latest_pack.case_completion_datetime, ia.submit_datetime
    )

    return LicenceSerializer(
        reference=licence_ref,
        start_date=latest_pack.licence_start_date,
        end_date=latest_pack.licence_end_date,
        status=latest_pack.status,
        licence_type="Paper" if latest_pack.issue_paper_licence_only else "Electronic",
        latest_case_closed_datetime=latest_pack.case_completion_datetime,
        initial_case_closed_datetime=initial_case_completion_datetime,
        time_to_initial_close=time_to_initial_close,
    )


def get_variation_number(ia: ImportApplication) -> int:
    reference = ia.reference or ""
    variation_info = reference.split("/")[3:]
    if variation_info:
        return int(variation_info[0])
    return 0


def get_licence_dates(licence: LicenceSerializer) -> str:
    if not licence.start_date or not licence.end_date:
        return ""
    return f"{licence.start_date.strftime('%d %b %Y')} - {licence.end_date.strftime('%d %b %Y')}"


def get_business_days(start_date: dt.date, end_date: dt.date) -> int:
    date_diff = end_date - start_date
    business_days = 0
    for i in range(date_diff.days + 1):
        day = start_date + dt.timedelta(days=i)
        if day.weekday() < 5:
            business_days += 1
    return business_days


def format_time_delta(from_datetime: dt.datetime, to_datetime: dt.datetime) -> str:
    if not from_datetime or not to_datetime:
        return ""
    time_delta = from_datetime - to_datetime
    hours = time_delta.seconds // 3600
    minutes = (time_delta.seconds % 3600) // 60
    return f"{time_delta.days}d {hours}h {minutes}m"


def get_constabularies(ia: FaImportApplication) -> str:
    if ia.process_type == ProcessTypes.FA_DFL:
        return ia.constabulary.name if ia.constabulary else ""
    return ", ".join(ia.user_imported_certificates.values_list("constabulary__name", flat=True))


def get_constabulary_email_times(ia: FaImportApplication) -> ConstabularyEmailTimesSerializer:
    constabulary_emails = ia.case_emails.filter(
        template_code=EmailTypes.CONSTABULARY_CASE_EMAIL,
    )
    if constabulary_emails:
        first_email_sent = constabulary_emails.first().sent_datetime
        last_email_closed = constabulary_emails.last().closed_datetime
    else:
        first_email_sent = None
        last_email_closed = None
    return ConstabularyEmailTimesSerializer(
        first_email_sent=first_email_sent, last_email_closed=last_email_closed
    )


def format_parameters_used(schedule_report: ScheduleReport) -> dict[str, str]:
    parameters = {}
    for desc, value in schedule_report.parameters.items():
        if desc in ["date_from", "date_to"]:
            value = dt.datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y") if value else ""
        elif desc == "application_type":
            if schedule_report.report.report_type == ReportType.IMPORT_LICENCES:
                value = ImportApplicationType.Types(value).label if value else "All"
            else:
                value = ExportApplicationType.Types(value).label if value else "All"
        elif desc == "date_filter_type":
            value = DateFilterType(value).label
        elif desc == "legislation":
            value = (
                "<br>".join(
                    ProductLegislation.objects.filter(pk__in=value).values_list("name", flat=True)
                )
                if value
                else "All"
            )
        parameters[format_label(desc)] = value
    return parameters
