import datetime as dt
from typing import Annotated, Any

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


def format_label(string: str) -> str:
    words = []
    for word in string.split("_"):
        if word in ["hse", "beis", "fir"]:
            words.append(word.upper())
        elif word in ["to", "of", "with"]:
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words)


class BaseSerializer(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        alias_generator=pydantic.AliasGenerator(
            serialization_alias=format_label,
        )
    )


class IssuedCertificateReportSerializer(BaseSerializer):
    certificate_reference: str
    case_reference: str
    application_type: str
    submitted_datetime: datetime_or_empty
    issue_datetime: datetime_or_empty
    case_processing_time: str
    total_processing_time: str
    exporter: str
    contact_full_name: str
    agent: str_or_empty
    country: str
    is_manufacturer: str
    responsible_person_statement: str
    countries_of_manufacture: str
    product_legislation: str
    hse_email_count: int
    beis_email_count: int
    application_update_count: int
    fir_count: int
    business_days_to_process: int
    continent: str_or_empty


class ImporterAccessRequestReportSerializer(BaseSerializer):
    request_date: date_or_empty
    request_type: str
    name: str = pydantic.Field(serialization_alias="Importer Name")
    address: str = pydantic.Field(serialization_alias="Importer Address")
    agent_name: str
    agent_address: str
    response: str
    response_reason: str


class ExporterAccessRequestReportSerializer(ImporterAccessRequestReportSerializer):
    name: str = pydantic.Field(serialization_alias="Exporter Name")
    address: str = pydantic.Field(serialization_alias="Exporter Address")


class AccessRequestTotalsReportSerializer(BaseSerializer):
    total_requests: int
    approved_requests: int
    refused_requests: int


class ImportLicenceSerializer(BaseSerializer):
    case_reference: str = pydantic.Field(serialization_alias="Case Ref")
    licence_reference: str_or_empty = pydantic.Field(serialization_alias="Licence Ref")
    licence_type: str
    under_appeal: str
    ima_type: str
    ima_type_title: str_or_empty
    ima_sub_type: str_or_empty
    variation_number: int = pydantic.Field(serialization_alias="Variation No")
    status: str
    ima_sub_type_title: str_or_empty
    importer: str = pydantic.Field(serialization_alias="Importer Name")
    agent_name: str_or_empty
    app_contact_name: str_or_empty
    country_of_origin: str_or_empty = pydantic.Field(serialization_alias="Coo Country Name")
    country_of_consignment: str_or_empty = pydantic.Field(serialization_alias="Coc Country Name")
    shipping_year: str | int
    com_group_name: str_or_empty
    commodity_codes: str
    initial_submitted_datetime: datetime_or_empty
    initial_case_closed_datetime: datetime_or_empty
    time_to_initial_close: str
    latest_case_closed_datetime: datetime_or_empty
    licence_dates: str
    licence_start_date: date_or_empty
    licence_expiry_date: date_or_empty = pydantic.Field(serialization_alias="Licence End Date")
    importer_printable: bool


class SupplementaryFirearmsSerializer(BaseSerializer):
    licence_reference: str_or_empty
    case_reference: str
    case_type: str
    importer: str
    eori_number: str_or_empty
    importer_address: str
    licence_start_date: date_or_empty | str
    licence_expiry_date: date_or_empty | str
    country_of_origin: str
    country_of_consignment: str
    endorsements: str
    constabularies: str_or_empty
    report_date: date_or_empty
    goods_description: str
    goods_quantity: int
    firearms_exceed_quantity: yes_no
    goods_description_with_subsection: str
    who_bought_from_name: str
    who_bought_from_reg_no: str_or_empty
    who_bought_from_address: str
    frame_serial_number: str_or_empty
    make_model: str_or_empty = pydantic.Field(serialization_alias="Make/Model")  # /PS-IGNORE
    calibre: str_or_empty
    proofing: str = pydantic.Field(serialization_alias="Gun Barrel Proofing meets CIP")
    firearms_document: str
    date_firearms_received: date_or_empty
    means_of_transport: str_or_empty
    all_reported: yes_no = pydantic.Field(serialization_alias="Reported all firearms for licence")


class BaseFirearmsLicenceSerializer(BaseSerializer):
    licence_reference: str_or_empty
    variation_number: int = pydantic.Field(serialization_alias="Licence Variation Number")
    case_reference: str
    importer: str
    eori_number: str_or_empty = pydantic.Field(serialization_alias="TURN Number")
    importer_address: str
    first_submitted_date: date_or_empty
    final_submitted_date: date_or_empty
    licence_start_date: date_or_empty
    licence_expiry_date: date_or_empty
    country_of_origin: str
    country_of_consignment: str
    endorsements: str
    revoked: yes_no


class DFLFirearmsLicenceSerializer(BaseFirearmsLicenceSerializer):
    goods_description: str


class OILFirearmsLicenceSerializer(BaseFirearmsLicenceSerializer):
    constabularies: str
    first_constabulary_email_sent_date: datetime_or_empty
    last_constabulary_email_closed_date: datetime_or_empty


class SILFirearmsLicenceSerializer(BaseFirearmsLicenceSerializer):
    goods_description: str
    constabularies: str
    first_constabulary_email_sent_date: datetime_or_empty
    last_constabulary_email_closed_date: datetime_or_empty


class LicenceSerializer(pydantic.BaseModel):
    reference: str_or_empty
    start_date: dt.date | None
    end_date: dt.date | None
    status: str_or_empty
    licence_type: str
    initial_case_closed_datetime: dt.datetime | None
    latest_case_closed_datetime: dt.datetime | None
    time_to_initial_close: str


class ConstabularyEmailTimesSerializer(pydantic.BaseModel):
    first_email_sent: datetime_or_empty
    last_email_closed: datetime_or_empty


class GoodsSectionSerializer(pydantic.BaseModel):
    description: str
    quantity: int | None
    unlimited_quantity: bool = False
    obsolete_calibre: str | None = None


class ErrorSerializer(BaseSerializer):
    report_name: str
    identifier: str
    error_type: str
    error_message: str
    column: str
    value: Any
