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
