from datetime import date, datetime
from typing import Annotated

import pydantic

CustomDateTime = Annotated[
    datetime,
    pydantic.PlainSerializer(
        lambda _datetime: _datetime.strftime("%d/%m/%Y %H:%M:%S"), return_type=str
    ),
]

CustomDate = Annotated[
    date,
    pydantic.PlainSerializer(lambda _date: _date.strftime("%d/%m/%Y"), return_type=str),
]


class IssuedCertificateReportSerializer(pydantic.BaseModel):
    certificate_reference: str = pydantic.Field(serialization_alias="Certificate Reference")
    case_reference: str = pydantic.Field(serialization_alias="Case Reference")
    application_type: str = pydantic.Field(serialization_alias="Application Type")
    submitted_datetime: CustomDateTime = pydantic.Field(serialization_alias="Submitted Datetime")
    issue_datetime: CustomDateTime = pydantic.Field(serialization_alias="Issue Datetime")
    case_processing_time: str = pydantic.Field(serialization_alias="Case Processing Time")
    total_processing_time: str = pydantic.Field(serialization_alias="Total Processing Time")
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
    request_date: CustomDate = pydantic.Field(serialization_alias="Request Date")
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
