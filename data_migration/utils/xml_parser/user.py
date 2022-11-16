from typing import Optional

from django.db.models import Model
from lxml import etree

from data_migration import models as dm
from data_migration.utils.format import datetime_or_none, get_xml_val

from .base import BaseXmlParser, FIRBaseParser


class ApprovalRequestParser(BaseXmlParser):
    MODEL = dm.ApprovalRequest
    FIELD = "approval_xml"
    ROOT_NODE = "/REQUEST_APPROVAL"
    PARENT = dm.AccessRequest
    IS_PROCESS = True

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[Model]:
        """Example XML

        <REQUEST_APPROVAL>
          <IMPORTER_ID />
          <EXPORTER_ID />
          <STATUS />
          <CONTACT_WUA_ID />
          <REQUEST_DATE />
          <REQUEST_CREATED_BY_WUA_ID />
          <REQUESTER_NAME />
          <RESPONSE_DATE />
          <RESPONDED_BY_WUA_ID />
          <RESPONDER_NAME />
          <RESPONSE />
          <RESPONSE_REASON />
        </REQUEST_APPROVAL>
        """

        status = get_xml_val(xml, "./STATUS")
        request_date = datetime_or_none(get_xml_val(xml, "./REQUEST_DATE"))
        requested_by = 2  # get_xml_val(xml, "./REQUEST_CREATED_BY_WUA_ID")
        requested_from = 2  # get_xml_val(xml, "./CONTACT_WUA_ID") ?
        response = get_xml_val(xml, "./RESPONSE")
        response_by = 2  # get_xml_val(xml, "./RESPONDED_BY_WUA_ID")
        response_date = datetime_or_none(get_xml_val(xml, "./RESPONSE_DATE"))
        response_reason = get_xml_val(xml, "./RESPONSE_REASON")

        return cls.MODEL(
            **{
                "access_request_id": parent_pk,
                "status": status,
                "request_date": request_date,
                "requested_by_id": requested_by,
                "requested_from_id": requested_from,
                "response": response,
                "response_by_id": response_by,
                "response_date": response_date,
                "response_reason": response_reason,
            }
        )

    @classmethod
    def add_process_model(cls, process_pk: int, xml: etree.ElementTree) -> dm.Process:
        status = get_xml_val(xml, "./STATUS")
        created = datetime_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_DATETIME"))
        importer = bool(get_xml_val(xml, "./IMPORTER_ID"))

        process_type = "ImporterApprovalRequest" if importer else "ExporterApprovalRequest"

        return dm.Process(
            id=process_pk,
            process_type=process_type,
            is_active=status != "DELETED",
            created=created,
        )


class AccessFIRParser(FIRBaseParser):
    MODEL = dm.FurtherInformationRequest
    FIELD = "fir_xml"
    ROOT_NODE = "/RFI_LIST/RFI"
    PARENT = dm.AccessRequest
    PARENT_MODEL_FIELD = "access_request_id"
