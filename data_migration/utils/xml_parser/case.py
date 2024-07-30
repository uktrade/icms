from django.db.models import Model
from lxml import etree

from data_migration import models as dm
from data_migration.utils.format import (
    date_or_none,
    date_to_timezone,
    datetime_or_none,
    get_xml_val,
    int_or_none,
    str_to_bool,
)

from .base import BaseXmlParser, FIRBaseParser


class VariationImportParser(BaseXmlParser):
    MODEL = dm.VariationRequest
    FIELD = "variations_xml"
    ROOT_NODE = "/VARIATION_REQUEST_LIST/VARIATION_REQUEST"
    PARENT = dm.ImportApplication

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
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
          <REJECT_PENDING_FLAG />
          <UPDATE_REQUEST_LIST>
            <UPDATE_REQUEST>
              <STATUS />
              <REQUEST_DATETIME />
              <REQUEST_BY_NAME />
              <REQUEST_BY_WUA_ID />
              <RESPONSE_DATETIME />
              <RESPONSE_BY_NAME />
              <RESPONSE_BY_WUA_ID />
              <REQUEST_TEXT />
            </UPDATE_REQUEST>
          </UPDATE_REQUEST_LIST>
        </VARIATION_REQUEST>
        """

        requested_date = date_or_none(get_xml_val(xml, "./REQUEST_DATE"))

        if not requested_date:
            return None

        status = get_xml_val(xml, "./STATUS")
        is_active = status == "OPEN"
        requested_datetime = date_to_timezone(requested_date)
        requested_by_id = int_or_none(get_xml_val(xml, "./REQUEST_BY_WUA_ID"))
        what_varied = get_xml_val(xml, "./WHAT_VARIED")
        why_varied = get_xml_val(xml, "./WHY_VARIED")
        when_varied = date_or_none(get_xml_val(xml, "./DATE_VARIED"))
        extension_flag = str_to_bool(get_xml_val(xml, "./EXTENSION_FLAG"))
        reject_cancellation_reason = get_xml_val(xml, "./REJECT_REASON")
        closed_date = date_or_none(get_xml_val(xml, "./CLOSED_DATE"))
        closed_datetime = date_to_timezone(closed_date)
        closed_by_id = int_or_none(get_xml_val(xml, "./CLOSED_BY_WUA_ID"))

        # populate this field if there is an open variation update request, else None
        update_request_reason = get_xml_val(
            xml, './UPDATE_REQUEST_LIST/UPDATE_REQUEST[STATUS/text()="OPEN"]/REQUEST_TEXT/text()'
        )

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "status": status,
                "is_active": is_active,
                "requested_datetime": requested_datetime,
                "requested_by_id": requested_by_id,
                "what_varied": what_varied,
                "why_varied": why_varied,
                "when_varied": when_varied,
                "extension_flag": extension_flag or False,
                "reject_cancellation_reason": reject_cancellation_reason,
                "closed_datetime": closed_datetime,
                "closed_by_id": closed_by_id,
                "update_request_reason": update_request_reason,
            }
        )


class VariationExportParser(BaseXmlParser):
    MODEL = dm.VariationRequest
    FIELD = "variations_xml"
    ROOT_NODE = "/VARIATION_LIST/VARIATION"
    PARENT = dm.ExportApplication
    REVERSE_LIST = True

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <VARIATION>
          <VARIATION_ID />
          <STATUS />
          <OPEN>
            <OPENED_DATETIME />
            <OPENED_BY_WUA_ID />
            <BODY />
          </OPEN>
          <CLOSE>
            <CLOSED_DATETIME />
            <CLOSED_BY_WUA_ID />
          </CLOSE>
          <CANCEL>
            <CANCELLED_DATETIME />
            <CANCELLED_BY_WUA_ID />
          </CANCEL>
          <WITHDRAW>
            <WITHDRAWN_DATETIME />
            <WITHDRAWN_BY_WUA_ID />
          </WITHDRAW>
          <DELETE>
            <DELETED_DATETIME />
            <DELETED_BY_WUA_ID />
          </DELETE>
        </VARIATION>
        """

        what_varied = get_xml_val(xml, "./OPEN/BODY")
        requested_datetime = datetime_or_none(get_xml_val(xml, "./OPEN/OPENED_DATETIME"))

        if not what_varied or not requested_datetime:
            return None

        status = get_xml_val(xml, "./STATUS")
        is_active = status == "OPEN"
        requested_by_id = int_or_none(get_xml_val(xml, "./OPEN/OPENED_BY_WUA_ID"))
        closed_datetime = datetime_or_none(get_xml_val(xml, "./CLOSE/CLOSED_DATETIME"))
        closed_by_id = int_or_none(get_xml_val(xml, "./CLOSED/CLOSED_BY_WUA_ID"))

        return cls.MODEL(
            **{
                "export_application_id": parent_pk,
                "status": status,
                "is_active": is_active,
                "requested_datetime": requested_datetime,
                "requested_by_id": requested_by_id,
                "what_varied": what_varied,
                "closed_datetime": closed_datetime,
                "closed_by_id": closed_by_id,
            }
        )


class CaseNoteExportParser(BaseXmlParser):
    MODEL = dm.CaseNote
    PARENT = dm.ExportApplication
    FIELD = "case_note_xml"
    ROOT_NODE = "/NOTE_LIST/NOTE"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
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
        created_by_id = int_or_none(get_xml_val(xml, "./CREATE/CREATED_BY_WUA_ID"))
        folder_id = int_or_none(get_xml_val(xml, "./FOLDER_ID"))

        return cls.MODEL(
            **{
                "export_application_id": parent_pk,
                "status": status if status in ["COMPLETED", "DELETED"] else "DRAFT",
                "note": note,
                "create_datetime": create_datetime,
                "created_by_id": created_by_id,
                "doc_folder_id": folder_id,
            }
        )


class FIRExportParser(FIRBaseParser):
    MODEL = dm.FurtherInformationRequest
    PARENT = dm.ExportApplication
    FIELD = "fir_xml"
    ROOT_NODE = "/RFI_LIST/RFI"
    PARENT_MODEL_FIELD = "export_application_id"


class UpdateExportParser(BaseXmlParser):
    MODEL = dm.UpdateRequest
    PARENT = dm.ExportApplication
    FIELD = "update_request_xml"
    ROOT_NODE = "/UPDATE_LIST/UPDATE"
    REVERSE_LIST = True

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
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
        requested_by_id = int_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_BY_WUA_ID"))
        response_detail = get_xml_val(xml, "./RESPONSE/RESPONSE_DETAILS")
        response_datetime = datetime_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_DATETIME"))
        response_by_id = int_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_BY_WUA_ID"))
        closed_datetime = datetime_or_none(get_xml_val(xml, "./CLOSE/CLOSED_DATETIME"))
        closed_by_id = int_or_none(get_xml_val(xml, "./CLOSE/CLOSED_BY_WUA_ID"))

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


class WithdrawalImportParser(BaseXmlParser):
    MODEL = dm.WithdrawApplication
    PARENT = dm.ImportApplication
    FIELD = "withdrawal_xml"
    ROOT_NODE = "/WITHDRAW_LIST/WITHDRAW"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <WITHDRAW>
          <WITHDRAW_STATUS />
          <WITHDRAW_REASON />
          <WITHDRAW_REQUESTER_WUA />
          <WITHDRAW_REQUESTED_DATE />
          <WITHDRAW_REQUESTER_FULLNAME />
          <WITHDRAW_DECISION />
          <WITHDRAW_REJECT_REASON />
          <WITHDRAW_RESPONDER_WUA />
          <WITHDRAW_RESPONDER_FULLNAME />
        </WITHDRAW>
        """

        status = get_xml_val(xml, "./WITHDRAW_STATUS")
        reason = get_xml_val(xml, "./WITHDRAW_REASON")
        created_date = datetime_or_none(get_xml_val(xml, "./WITHDRAW_REQUESTED_DATE"), True)

        if not reason or not created_date:
            return None

        request_by_id = int_or_none(get_xml_val(xml, "./WITHDRAW_REQUESTER_WUA"))
        response = get_xml_val(xml, "./WITHDRAW_REJECT_REASON")
        response_by_id = int_or_none(get_xml_val(xml, "./WITHDRAW_RESPONDER_WUA"))
        updated_date = datetime_or_none(get_xml_val(xml, "./WITHDRAW_RESPONDED_DATE"), True)

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "is_active": status == "OPEN",
                "status": status,
                "reason": reason,
                "request_by_id": request_by_id,
                "response": response or "",
                "response_by_id": response_by_id,
                "created_datetime": created_date,
                "updated_datetime": updated_date or created_date,
            }
        )


class WithdrawalExportParser(BaseXmlParser):
    MODEL = dm.WithdrawApplication
    PARENT = dm.ExportApplication
    FIELD = "withdrawal_xml"
    ROOT_NODE = "/WITHDRAWAL_LIST/WITHDRAWAL"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <WITHDRAWAL>
          <WITHDRAWAL_ID />
          <STATUS />
          <REQUEST>
            <REQUESTED_DATETIME />
            <REQUESTED_BY_WUA_ID />
            <BODY />
          </REQUEST>
          <RESPONSE>
            <RESPONDED_DATETIME />
            <RESPONDED_BY_WUA_ID />
            <DECISION />
            <REJECT_REASON />
          </RESPONSE>
          <DELETE>
            <DELETED_DATETIME />
            <DELETED_BY_WUA_ID />
          </DELETE>
          <RETRACT_LIST />
        </WITHDRAWAL>
        """

        status = get_xml_val(xml, "./STATUS")
        reason = get_xml_val(xml, "./REQUEST/BODY")
        created_datetime = datetime_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_DATETIME"))

        if not reason or not created_datetime:
            return None

        request_by_id = int_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_BY_WUA_ID"))
        response = get_xml_val(xml, "./RESPONSE/REJECT_REASON")
        response_by_id = int_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_BY_WUA_ID"))
        updated_datetime = datetime_or_none(
            get_xml_val(xml, "./DELETE/DELETED_DATETIME")
        ) or datetime_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_DATETIME"))

        return cls.MODEL(
            **{
                "export_application_id": parent_pk,
                "is_active": status == "OPEN",
                "status": status,
                "reason": reason,
                "request_by_id": request_by_id,
                "response": response or "",
                "response_by_id": response_by_id,
                "created_datetime": created_datetime,
                "updated_datetime": updated_datetime or created_datetime,
            }
        )
