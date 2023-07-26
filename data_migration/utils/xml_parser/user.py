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
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
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

        if not request_date:
            return None

        requested_by = get_xml_val(xml, "./REQUEST_CREATED_BY_WUA_ID")
        requested_from = get_xml_val(xml, "./CONTACT_WUA_ID")  # TODO check post-migrate
        response = get_xml_val(xml, "./RESPONSE")
        response_by = get_xml_val(xml, "./RESPONDED_BY_WUA_ID")
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
        created = datetime_or_none(get_xml_val(xml, "./REQUEST_DATE"))
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


class PhoneNumberParser(BaseXmlParser):
    MODEL = dm.PhoneNumber
    FIELD = "telephone_xml"
    ROOT_NODE = "/TELEPHONE_NO_LIST/TELEPHONE_NO"
    PARENT = dm.User

    TYPES = {
        "F": "FAX",
        "H": "HOME",
        "M": "MOBILE",
        "W": "WORK",
    }

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <TELEPHONE_NO>
          <TELEPHONE_HASH_CODE />
          <TYPE />
          <COMMENT />
        </TELEPHONE_NO>
        """

        phone_number = get_xml_val(xml, "./TELEPHONE_HASH_CODE")
        phone_type = get_xml_val(xml, "./TYPE")
        comment = get_xml_val(xml, "./COMMENT")

        return cls.MODEL(
            **{
                "user_id": parent_pk,
                "phone": phone_number,
                "type": cls.TYPES[phone_type],
                "comment": comment,
            }
        )


class EmailAddressParser(BaseXmlParser):
    PARENT = dm.User
    MODEL = dm.Email

    TYPES = {
        "H": "HOME",
        "W": "WORK",
    }

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <PERSONAL_EMAIL>
          <EMAIL_ADDRESS />
          <PORTAL_NOTIFICATIONS />
          <TYPE />
          <COMMENT />
        </PERSONAL_EMAIL>
        """

        email_type = get_xml_val(xml, "./TYPE")
        portal = get_xml_val(xml, "./PORTAL_NOTIFICATIONS")
        email = get_xml_val(xml, "./EMAIL_ADDRESS")

        if not email:
            return None

        data = {
            "user_id": parent_pk,
            "email": email,
            "comment": get_xml_val(xml, "./COMMENT"),
            "type": cls.TYPES[email_type],
            "portal_notifications": portal in ("Primary", "Yes"),
            "is_primary": portal == "Primary",
        }

        return cls.MODEL(**data)


class PersonalEmailAddressParser(EmailAddressParser):
    FIELD = "personal_email_xml"
    ROOT_NODE = "/PERSONAL_EMAIL_LIST/PERSONAL_EMAIL"


class AlternativeEmailAddressParser(EmailAddressParser):
    FIELD = "alternative_email_xml"
    ROOT_NODE = "/DISTRIBUTION_EMAIL_LIST/DISTRIBUTION_EMAIL"
