import datetime as dt

from django.db.models import QuerySet

from web.models import (
    ExportApplicationType,
    ImportApplicationType,
    ProductLegislation,
    Report,
    ScheduleReport,
    User,
)
from web.permissions import get_report_type_for_permission

from .constants import DateFilterType, ReportType, UserDateFilterType
from .serializers import (
    ConstabularyEmailTimesSerializer,
    ErrorSerializer,
    LicenceSerializer,
    format_label,
)


def get_licence_details(ia: dict) -> LicenceSerializer:
    if ia["latest_licence_cdr_data"]:
        licence = LicenceSerializer(
            start_date=ia["latest_licence_start_date"],
            end_date=ia["latest_licence_end_date"],
            licence_type=(
                "Paper" if ia["latest_licence_issue_paper_licence_only"] else "Electronic"
            ),
            status=ia["latest_licence_status"],
            reference=ia["latest_licence_cdr_data"][0][1],
            latest_case_closed_datetime=ia["latest_licence_case_completion_datetime"],
            initial_case_closed_datetime=ia["initial_case_closed_datetime"],
            time_to_initial_close=format_time_delta(
                ia["latest_licence_case_completion_datetime"], ia["submit_datetime"]
            ),
        )
    else:
        licence = LicenceSerializer(
            reference="",
            start_date=None,
            end_date=None,
            status=None,
            licence_type="Electronic",
            latest_case_closed_datetime=None,
            initial_case_closed_datetime=None,
            time_to_initial_close="",
        )
    return licence


def get_variation_number(reference: str) -> int:
    reference = reference or ""
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


def get_constabulary_email_times(ia: dict) -> ConstabularyEmailTimesSerializer:
    return ConstabularyEmailTimesSerializer(
        first_email_sent=ia["constabulary_email_first_email_sent"],
        last_email_closed=ia["constabulary_email_last_email_closed"],
    )


def format_contact_name(title: str | None, first_name: str | None, last_name: str | None) -> str:
    name_parts = [title, first_name, last_name]
    return " ".join(filter(None, name_parts))


def format_parameters_used(schedule_report: ScheduleReport) -> dict[str, str]:
    parameters = {}
    for desc, value in schedule_report.parameters.items():
        if desc in [
            "date_from",
            "date_to",
            "case_closed_date_from",
            "case_closed_date_to",
            "case_submitted_date_from",
            "case_submitted_date_to",
        ]:
            value = dt.datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y") if value else ""
        elif desc == "application_type":
            try:
                if schedule_report.report.report_type == ReportType.IMPORT_LICENCES:
                    value = ImportApplicationType.Types(value).label if value else "All"
                else:
                    value = ExportApplicationType.Types(value).label if value else "All"
            except ValueError:
                pass
        elif desc == "date_filter_type":
            if schedule_report.report.report_type == ReportType.ACTIVE_USERS:
                value = UserDateFilterType(value).label
            else:
                value = DateFilterType(value).label
        elif desc == "legislation":
            value = (
                "<br>".join(
                    ProductLegislation.objects.filter(pk__in=value).values_list("name", flat=True)
                )
                if value
                else "All"
            )
        elif desc == "is_legacy_report":
            value = "Yes" if value else "No"
        parameters[format_label(desc)] = value
    return parameters


def format_importer_address(ia: QuerySet) -> str:
    address = [
        ia["importer_address_1"],
        ia["importer_address_2"],
        ia["importer_address_3"],
        ia["importer_address_4"],
        ia["importer_address_5"],
        ia["importer_postcode"],
    ]
    return ", ".join(f for f in address if f)


def get_error_serializer_header() -> list[str]:
    schema = ErrorSerializer.model_json_schema(by_alias=True, mode="serialization")
    return schema["required"]


def get_report_objects_for_user(user: User) -> QuerySet[Report]:
    report_types = filter(
        None, [get_report_type_for_permission(perm) for perm in user.get_all_permissions()]
    )
    return Report.objects.filter(report_type__in=report_types)
