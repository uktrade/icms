from typing import Optional

from django.db.models import Model
from lxml import etree

from data_migration import models as dm
from data_migration.utils.format import (
    date_or_none,
    datetime_or_none,
    get_xml_val,
    int_or_none,
    str_to_bool,
)

from .base import BaseXmlParser


class VariationImportParser(BaseXmlParser):
    MODEL = dm.VariationRequest
    FIELD = "variations_xml"
    ROOT_NODE = "/VARIATION_REQUEST_LIST/VARIATION_REQUEST"
    PARENT = dm.ImportApplication

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[Model]:
        """Example XML

        <VARIATION_REQUEST>
          <EXTENSION_FLAG />
          <STATUS />
          <REQUEST_DATE />
          <REQUEST_BY_NAME />
          <REQUEST_BY_WUA_ID />
          <WHAT_VARIED />
          <WHY_VARIED />
          <DATE_VARIED />
          <REJECT_REASON />
          <CLOSED_DATE />
          <CLOSED_BY_NAME />
          <CLOSED_BY_WUA_ID />
          <UPDATE_REQUEST_LIST />
          <REJECT_PENDING_FLAG />
          <UPDATE_REQUEST_LIST />
        </VARIATION_REQUEST>
        """

        status = get_xml_val(xml, "./STATUS")
        is_active = status == "OPEN"
        requested_date = date_or_none(get_xml_val(xml, "./REQUEST_DATE"))
        requested_by_id = (
            2  # TODO ICMSLST-1324 int_or_none(get_xml_val(xml, "./REQUEST_BY_WUA_ID"))
        )
        what_varied = get_xml_val(xml, "./WHAT_VARIED")
        why_varied = get_xml_val(xml, "./WHY_VARIED")
        when_varied = date_or_none(get_xml_val(xml, "./DATE_VARIED"))
        extension_flag = str_to_bool(get_xml_val(xml, "./EXTENSION_FLAG"))
        reject_cancellation_reason = get_xml_val(xml, "./REJECT_REASON")
        closed_date = date_or_none(get_xml_val(xml, "./CLOSED_DATE"))
        closed_by_id = 2  # TODO ICMSLST-1324

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "status": status,
                "is_active": is_active,
                "requested_datetime": requested_date,
                "requested_by_id": requested_by_id,
                "what_varied": what_varied,
                "why_varied": why_varied,
                "when_varied": when_varied,
                "extension_flag": extension_flag,
                "reject_cancellation_reason": reject_cancellation_reason,
                "closed_datetime": closed_date,
                "closed_by_id": closed_by_id,
            }
        )


class CaseNoteExportParser(BaseXmlParser):
    MODEL = dm.CaseNote
    PARENT = dm.ExportApplication
    FIELD = "case_note_xml"
    ROOT_NODE = "/NOTE_LIST/NOTE"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[Model]:
        """Example XML

        <NOTE>
          <NOTE_ID />
          <STATUS />
          <IS_FOR_ATTENTION />
          <BODY />
          <CREATE>
           <CREATED_DATETIME />
           <CREATED_BY_WUA_ID />
          </CREATE>
          <LAST_UPDATE>
            <LAST_UPDATED_DATETIME />
            <LAST_UPDATED_BY_WUA_ID />
          </LAST_UPDATE>
          <FOLDER_ID />
        </NOTE>
        """
        status = get_xml_val(xml, "./STATUS")
        note = get_xml_val(xml, "./BODY")
        create_datetime = datetime_or_none(get_xml_val(xml, "./CREATE/CREATED_DATETIME"))
        created_by_id = 2  # int_or_none(get_xml_val(xml, './CREATE/CREATED_BY_WUA_ID'))
        folder_id = int_or_none(get_xml_val(xml, "./FOLDER_ID"))

        return cls.MODEL(
            **{
                "export_application_id": parent_pk,
                "is_active": status != "DELETED",
                "status": status if status == "COMPLETED" else "DRAFT",
                "note": note,
                "create_datetime": create_datetime,
                "created_by_id": created_by_id,
                "doc_folder_id": folder_id,
            }
        )


class FIRExportParser(BaseXmlParser):
    MODEL = dm.FurtherInformationRequest
    PARENT = dm.ExportApplication
    FIELD = "fir_xml"
    ROOT_NODE = "/RFI_LIST/RFI"
    REVERSE_LIST = True

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[Model]:
        """Example XML

        <RFI>
          <RFI_ID / >
          <CASE_RFI_REFERENCE />
          <STATUS />
          <REQUEST>
            <REQUESTED_DATETIME />
            <REQUESTED_BY_WUA_ID />
            <SUBJECT />
            <CC_EMAIL_LIST />
            <BODY />
          </REQUEST>
          <RESPONSE>
            <RESPONDED_DATETIME />
            <RESPONDED_BY_WUA_ID />
            <RESPONSE_DETAILS />
          </RESPONSE>
          <CLOSE>
            <CLOSED_DATETIME />
            <CLOSED_BY_WUA_ID />
          </CLOSE>
          <DELETE>
            <DELETED_DATETIME />
            <DELETED_BY_WUA_ID />
          </DELETE>
          <WITHDRAW_LIST />
        </RFI>
        """

        status = get_xml_val(xml, "./STATUS")
        request_subject = get_xml_val(xml, "./REQUEST/SUBJECT")
        request_detail = get_xml_val(xml, "./REQUEST/BODY")
        requested_by_id = 2  # int_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_BY_WUA_ID"))
        email_cc_address_list_str = get_xml_val(xml, "./REQUEST/CC_EMAIL_LIST")
        response_detail = get_xml_val(xml, "./RESPONSE/RESPONSE_DETAILS")
        response_datetime = datetime_or_none(get_xml_val(xml, "./RESPONSE/RESPONSED_DATETIME"))
        response_by_id = 2  # int_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_BY_WUA"))
        closed_datetime = datetime_or_none(get_xml_val(xml, "./CLOSE/CLOSED_DATETIME"))
        closed_by_id = 2  # int_or_none(get_xml_val(xml, "./CLOSE/CLOSED_BY_WUA_ID"))
        deleted_datetime = datetime_or_none(get_xml_val(xml, "./DELETE/DELETED_DATETIME"))
        deleted_by_id = 2  # int_or_none(get_xml_val(xml, "./DELETE/DELETED_BY_WUA_ID"))

        return cls.MODEL(
            **{
                "export_application_id": parent_pk,
                "status": status,
                "request_subject": request_subject,
                "request_detail": request_detail,
                "requested_by_id": requested_by_id,
                "email_cc_address_list_str": email_cc_address_list_str,
                "response_detail": response_detail,
                "response_datetime": response_datetime,
                "response_by_id": response_by_id,
                "closed_datetime": closed_datetime,
                "closed_by_id": closed_by_id,
                "deleted_datetime": deleted_datetime,
                "deleted_by_id": deleted_by_id,
            }
        )

    @classmethod
    def add_process_model(cls, process_pk: int, xml: etree.ElementTree) -> dm.Process:
        status = get_xml_val(xml, "./STATUS")
        created = datetime_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_DATETIME"))
        return dm.Process(
            id=process_pk,
            process_type="FurtherInformationRequest",
            is_active=status != "DELETED",
            created=created,
        )


class UpdateExportParser(BaseXmlParser):
    MODEL = dm.UpdateRequest
    PARENT = dm.ExportApplication
    FIELD = "update_request_xml"
    ROOT_NODE = "/UPDATE_LIST/UPDATE"
    REVERSE_LIST = True

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[Model]:
        """Example XML

        <UPDATE>
          <UPDATE_ID />
          <STATUS />
          <REQUEST>
            <REQUESTED_DATETIME />
            <REQUESTED_BY_WUA_ID />
            <SUBJECT />
            <CC_EMAIL_LIST />
            <BODY />
          </REQUEST>
          <RESPONSE>
            <RESPONDED_DATETIME />
            <RESPONDED_BY_WUA_ID />
            <SUMMARY_OF_CHANGES />
          </RESPONSE>
          <CLOSE>
            <CLOSED_DATETIME/>
            <CLOSED_BY_WUA_ID/>
          </CLOSE>
          <DELETE>
            <DELETED_DATETIME />
            <DELETED_BY_WUA_ID />
          </DELETE>
          <WITHDRAW_LIST/>
        </UPDATE>
        """

        status = get_xml_val(xml, "./STATUS")
        request_subject = get_xml_val(xml, "./REQUEST/SUBJECT")
        request_detail = get_xml_val(xml, "./REQUEST/BODY")
        request_datetime = datetime_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_DATETIME"))
        requested_by_id = 2  # int_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_BY_WUA_ID"))
        response_detail = get_xml_val(xml, "./RESPONSE/RESPONSE_DETAILS")
        response_datetime = datetime_or_none(get_xml_val(xml, "./RESPONSE/RESPONSED_DATETIME"))
        response_by_id = 2  # int_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_BY_WUA"))
        closed_datetime = datetime_or_none(get_xml_val(xml, "./CLOSE/CLOSED_DATETIME"))
        closed_by_id = 2  # int_or_none(get_xml_val(xml, "./CLOSE/CLOSED_BY_WUA_ID"))

        return cls.MODEL(
            **{
                "export_application_id": parent_pk,
                "is_active": status != "DELETED",
                "status": status,
                "request_subject": request_subject,
                "request_detail": request_detail,
                "requested_by_id": requested_by_id,
                "request_datetime": request_datetime,
                "response_detail": response_detail,
                "response_datetime": response_datetime,
                "response_by_id": response_by_id,
                "closed_datetime": closed_datetime,
                "closed_by_id": closed_by_id,
            }
        )
