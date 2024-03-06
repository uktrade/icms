import datetime as dt
from typing import Annotated

import pydantic

from web.models.shared import YesNoChoices

datetime_or_empty = Annotated[
    dt.datetime | None,
    pydantic.PlainSerializer(
        lambda _datetime: (
            _datetime.strftime("%d/%m/%Y %H:%M:%S") if hasattr(_datetime, "strftime") else ""
        ),
        return_type=str,
    ),
]

date_or_empty = Annotated[
    dt.date | None,
    pydantic.PlainSerializer(
        lambda _date: _date.strftime("%d/%m/%Y") if hasattr(_date, "strftime") else "",
        return_type=str,
    ),
]

str_or_empty = Annotated[
    str | None,
    pydantic.PlainSerializer(
        lambda _str: _str if _str else "",
        return_type=str,
    ),
]


yes_no = Annotated[
    bool | None,
    pydantic.PlainSerializer(
        lambda _bool: YesNoChoices.yes.title() if _bool else YesNoChoices.no.title(),
        return_type=str,
    ),
]


class IssuedCertificateReportSerializer(pydantic.BaseModel):
    certificate_reference: str = pydantic.Field(serialization_alias="Certificate Reference")
    case_reference: str = pydantic.Field(serialization_alias="Case Reference")
    application_type: str = pydantic.Field(serialization_alias="Application Type")
    submitted_datetime: datetime_or_empty = pydantic.Field(serialization_alias="Submitted Datetime")
    issue_datetime: datetime_or_empty = pydantic.Field(serialization_alias="Issue Datetime")
    case_processing_time: str = pydantic.Field(serialization_alias="Case Processing Time")
    total_processing_time: str = pydantic.Field(
        serialization_alias="Total Processing Time",
    )
    exporter: str = pydantic.Field(serialization_alias="Exporter")
    contact: str = pydantic.Field(serialization_alias="Contact Full Name")
    agent: str = pydantic.Field(serialization_alias="Agent")
    country: str = pydantic.Field(serialization_alias="Country")
    is_manufacturer: str = pydantic.Field(serialization_alias="Is Manufacturer")
    responsible_person_statement: str = pydantic.Field(
        serialization_alias="Responsible Person Statement"
    )
    countries_of_manufacture: str = pydantic.Field(serialization_alias="Countries of Manufacture")
    product_legislation: str = pydantic.Field(serialization_alias="Product Legislation")
    hse_email_count: int = pydantic.Field(serialization_alias="HSE Email Count")
    beis_email_count: int = pydantic.Field(serialization_alias="BEIS Email Count")
    application_update_count: int = pydantic.Field(serialization_alias="Application Update Count")
    fir_count: int = pydantic.Field(serialization_alias="FIR Count")
    business_days_to_process: int = pydantic.Field(serialization_alias="Business Days to Process")


class ImporterAccessRequestReportSerializer(pydantic.BaseModel):
    request_date: date_or_empty = pydantic.Field(serialization_alias="Request Date")
    request_type: str = pydantic.Field(serialization_alias="Request Type")
    name: str = pydantic.Field(serialization_alias="Importer Name")
    address: str = pydantic.Field(serialization_alias="Importer Address")
    agent_name: str = pydantic.Field(serialization_alias="Agent Name")
    agent_address: str = pydantic.Field(serialization_alias="Agent Address")
    response: str = pydantic.Field(serialization_alias="Response")
    response_reason: str = pydantic.Field(serialization_alias="Response Reason")


class ExporterAccessRequestReportSerializer(ImporterAccessRequestReportSerializer):
    name: str = pydantic.Field(serialization_alias="Exporter Name")
    address: str = pydantic.Field(serialization_alias="Exporter Address")


class AccessRequestTotalsReportSerializer(pydantic.BaseModel):
    total_requests: int = pydantic.Field(serialization_alias="Total Requests")
    approved_requests: int = pydantic.Field(serialization_alias="Approved Requests")
    refused_requests: int = pydantic.Field(serialization_alias="Refused Requests")


class ImportLicenceSerializer(pydantic.BaseModel):
    case_reference: str = pydantic.Field(serialization_alias="Case Ref")
    licence_reference: str_or_empty = pydantic.Field(serialization_alias="Licence Ref")
    licence_type: str = pydantic.Field(serialization_alias="Licence Type")
    under_appeal: str = pydantic.Field(serialization_alias="Under Appeal")
    ima_type: str = pydantic.Field(serialization_alias="Ima Type")
    ima_type_title: str_or_empty = pydantic.Field(serialization_alias="Ima Type Title")
    ima_sub_type: str_or_empty = pydantic.Field(serialization_alias="Ima Sub Type")
    variation_number: int = pydantic.Field(serialization_alias="Variation No")
    status: str = pydantic.Field(serialization_alias="Status")
    ima_sub_type_title: str_or_empty = pydantic.Field(serialization_alias="Ima Sub Type Title")
    importer_name: str = pydantic.Field(serialization_alias="Importer Name")
    agent_name: str_or_empty = pydantic.Field(serialization_alias="Agent Name")
    app_contact_name: str = pydantic.Field(serialization_alias="App Contact Name")
    coo_country_name: str = pydantic.Field(serialization_alias="Coo Country Name")
    coc_country_name: str = pydantic.Field(serialization_alias="Coc Country Name")
    shipping_year: str | int = pydantic.Field(serialization_alias="Shipping Year")
    com_group_name: str = pydantic.Field(serialization_alias="Com Group Name")
    commodity_codes: str = pydantic.Field(serialization_alias="Commodity Codes")
    initial_submitted_datetime: datetime_or_empty = pydantic.Field(
        serialization_alias="Initial Submitted Datetime"
    )
    initial_case_closed_datetime: datetime_or_empty = pydantic.Field(
        serialization_alias="Initial Case Closed Datetime"
    )
    time_to_initial_close: str = pydantic.Field(serialization_alias="Time to Initial Close")
    latest_case_closed_datetime: datetime_or_empty = pydantic.Field(
        serialization_alias="Latest Case Closed Datetime"
    )
    licence_dates: str = pydantic.Field(serialization_alias="Licence Dates")
    licence_start_date: date_or_empty = pydantic.Field(serialization_alias="Licence Start Date")
    licence_end_date: date_or_empty = pydantic.Field(serialization_alias="Licence End Date")
    importer_printable: bool = pydantic.Field(serialization_alias="Importer Printable")


class SupplementaryFirearmsSerializer(pydantic.BaseModel):
    licence_reference: str_or_empty = pydantic.Field(serialization_alias="Licence Reference")
    case_reference: str = pydantic.Field(serialization_alias="Case Reference")
    case_type: str = pydantic.Field(serialization_alias="Case Type")
    importer_name: str = pydantic.Field(serialization_alias="Importer")
    eori_number: str_or_empty = pydantic.Field(serialization_alias="Eori Number")
    importer_address: str = pydantic.Field(serialization_alias="Importer Address")
    licence_start_date: date_or_empty | str = pydantic.Field(
        serialization_alias="Licence Start Date"
    )
    licence_end_date: date_or_empty | str = pydantic.Field(
        serialization_alias="Licence Expiry Date"
    )
    coo_country_name: str = pydantic.Field(serialization_alias="Country of Origin")
    coc_country_name: str = pydantic.Field(serialization_alias="Country of Consignment")
    endorsements: str = pydantic.Field(serialization_alias="Endorsements")
    constabularies: str = pydantic.Field(serialization_alias="Constabularies")

    report_date: date_or_empty = pydantic.Field(serialization_alias="Report Date")
    goods_description: str = pydantic.Field(serialization_alias="Goods Description")
    goods_quantity: int = pydantic.Field(serialization_alias="Goods Quantity")
    exceed_quantity: yes_no = pydantic.Field(serialization_alias="Firearms Exceed Quantity")
    goods_description_with_sub_section: str = pydantic.Field(
        serialization_alias="Goods Description with Subsection"
    )
    bought_from: str = pydantic.Field(serialization_alias="Who Bought From Name")
    bought_from_reg_no: str_or_empty = pydantic.Field(serialization_alias="Who Bought From Reg No")
    bought_from_address: str = pydantic.Field(
        serialization_alias="Who Bought From Address"  # /PS-IGNORE
    )
    frame_serial_number: str_or_empty = pydantic.Field(
        serialization_alias="Frame Serial Number"  # /PS-IGNORE
    )
    make_model: str_or_empty = pydantic.Field(serialization_alias="Make/Model")  # /PS-IGNORE
    calibre: str_or_empty = pydantic.Field(serialization_alias="Calibre")  # /PS-IGNORE
    proofing: str = pydantic.Field(serialization_alias="Gun Barrel Proofing meets CIP")
    firearms_document: str = pydantic.Field(serialization_alias="Firearms Document")  # /PS-IGNORE
    date_firearms_received: date_or_empty = pydantic.Field(
        serialization_alias="Date Firearms Received"  # /PS-IGNORE
    )
    transport: str_or_empty = pydantic.Field(serialization_alias="Means of Transport")  # /PS-IGNORE
    all_reported: yes_no = pydantic.Field(serialization_alias="Reported all firearms for licence")


class BaseFirearmsLicenceSerializer(pydantic.BaseModel):
    licence_reference: str_or_empty = pydantic.Field(serialization_alias="Licence Reference")
    variation_number: int = pydantic.Field(serialization_alias="Licence Variation Number")
    case_reference: str = pydantic.Field(serialization_alias="Case Reference")
    importer_name: str = pydantic.Field(serialization_alias="Importer")
    eori_number: str_or_empty = pydantic.Field(serialization_alias="TURN Number")
    importer_address: str = pydantic.Field(serialization_alias="Importer Address")
    submitted_datetime: date_or_empty = pydantic.Field(serialization_alias="First Submitted Date")
    last_submitted_datetime: date_or_empty = pydantic.Field(
        serialization_alias="Final Submitted Date"
    )
    licence_start_date: date_or_empty = pydantic.Field(serialization_alias="Licence Start Date")
    licence_end_date: date_or_empty = pydantic.Field(serialization_alias="Licence Expiry Date")
    coo_country_name: str = pydantic.Field(serialization_alias="Country of Origin")
    coc_country_name: str = pydantic.Field(serialization_alias="Country of Consignment")

    endorsements: str = pydantic.Field(serialization_alias="Endorsements")
    revoked: yes_no = pydantic.Field(serialization_alias="Revoked")


class DFLFirearmsLicenceSerializer(BaseFirearmsLicenceSerializer):
    goods_description: str = pydantic.Field(serialization_alias="Goods Description")


class OILFirearmsLicenceSerializer(BaseFirearmsLicenceSerializer):
    constabularies: str = pydantic.Field(serialization_alias="Constabularies")
    first_constabulary_email_sent: datetime_or_empty = pydantic.Field(
        serialization_alias="First Constabulary Email Sent Date"
    )
    last_constabulary_email_closed: datetime_or_empty = pydantic.Field(
        serialization_alias="Last Constabulary Email Closed Date"
    )


class SILFirearmsLicenceSerializer(BaseFirearmsLicenceSerializer):
    goods_description: str = pydantic.Field(serialization_alias="Goods Description")
    constabularies: str = pydantic.Field(serialization_alias="Constabularies")
    first_constabulary_email_sent: datetime_or_empty = pydantic.Field(
        serialization_alias="First Constabulary Email Sent Date"
    )
    last_constabulary_email_closed: datetime_or_empty = pydantic.Field(
        serialization_alias="Last Constabulary Email Closed Date"
    )


class LicenceSerializer(pydantic.BaseModel):
    reference: str_or_empty = pydantic.Field(serialization_alias="Licence Reference")
    start_date: dt.date | None = pydantic.Field(serialization_alias="Licence Start Date")
    end_date: dt.date | None = pydantic.Field(serialization_alias="Licence Expiry Date")
    status: str_or_empty = pydantic.Field(serialization_alias="Status")
    licence_type: str = pydantic.Field(serialization_alias="Licence Type")
    initial_case_closed_datetime: dt.datetime | None = pydantic.Field(
        serialization_alias="Initial Case Closed Datetime"
    )
    latest_case_closed_datetime: dt.datetime | None = pydantic.Field(
        serialization_alias="Latest Case Closed Datetime"
    )
    time_to_initial_close: str = pydantic.Field(serialization_alias="Time to Initial Close")


class ConstabularyEmailTimesSerializer(pydantic.BaseModel):
    first_email_sent: datetime_or_empty
    last_email_closed: datetime_or_empty
