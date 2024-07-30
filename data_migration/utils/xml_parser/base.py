from collections import defaultdict
from collections.abc import Generator

from django.db.models import Model, QuerySet
from lxml import etree

from data_migration.management.commands.utils.db import new_process_pk
from data_migration.models.flow import Process
from data_migration.utils.format import datetime_or_none, get_xml_val, int_or_none

BatchT = list[tuple]
ModelListT = dict[type[Model], list[Model]]


class BaseXmlParser:
    # The name of the node which the object data can be found
    ROOT_NODE: str = ""

    # The model to be populated by the parser
    MODEL: type[Model] | None = None

    # The model or list of models in which the xml data stored
    PARENT: list[type[Model]] | type[Model] | None = None

    # The name of the field the xml data is stored under
    FIELD: str = ""

    IS_PROCESS: bool = False

    REVERSE_LIST: bool = False

    @classmethod
    def get_queryset(cls) -> Generator:
        """Generates the queryset of values for the xml data.

        The default values are the parent model pk and the xml data as a string
        If there are multiple parents, create a union queryset of these values
        """

        if not cls.PARENT or not cls.FIELD:
            raise NotImplementedError("PARENT and FIELD must be defined on the parser")

        if isinstance(cls.PARENT, list):
            querysets = [
                parent.objects.filter(**{f"{cls.FIELD}__isnull": False}).values_list(
                    "pk", cls.FIELD
                )
                for parent in cls.PARENT
            ]
            return QuerySet.union(*querysets).iterator(chunk_size=2000)

        return (
            cls.PARENT.objects.filter(**{f"{cls.FIELD}__isnull": False})
            .values_list("pk", cls.FIELD)
            .iterator(chunk_size=2000)
        )

    @classmethod
    def parse_xml(cls, batch: BatchT) -> ModelListT:
        """Parses xml to bulk_create model objects from a list of xml strings

        :param batch: A list of parent_pk, xml string pairs.

        Example batch: [(1, "<ROOT><ELEMENT /></ROOT>"), (2, "<ROOT><ELEMENT></ROOT>")]
        Returns a dict with models of keys and a list of objects to populate them as values
        """
        model_lists: ModelListT = defaultdict(list)

        process_pk = int(cls.IS_PROCESS and new_process_pk())

        for pk, xml_str in batch:
            xml_tree = etree.fromstring(xml_str)
            xml_list = xml_tree.xpath(cls.ROOT_NODE)

            if cls.REVERSE_LIST:
                xml_list = xml_list[::-1]

            for xml in xml_list:
                obj = cls.parse_xml_fields(pk, xml)

                if not obj:
                    continue

                if cls.IS_PROCESS:
                    process = cls.add_process_model(process_pk, xml)
                    model_lists[Process].append(process)
                    obj.id = process_pk
                    process_pk += 1

                model_lists[obj._meta.model].append(obj)

        return model_lists

    @classmethod
    def add_process_model(cls, process_pk: int, xml: etree.ElementTree) -> Process:
        raise NotImplementedError("Extracting process model from XML must be defined")

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Retrieves data for fields from an ElementTree object

        :param parent_pk: The pk of the parent model
        :param xml: An xml tree from which the data for the model will be extracted
        """
        raise NotImplementedError("XML parsing must be defined")

    @classmethod
    def log_message(cls, idx: int) -> str:
        return f"{idx} - Running {cls.__name__}"


class FIRBaseParser(BaseXmlParser):
    REVERSE_LIST = True
    PARENT_MODEL_FIELD: str = ""
    IS_PROCESS = True

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
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
        if not cls.MODEL:
            raise NotImplementedError("MODEL must be defined on the parser")

        status = get_xml_val(xml, "./STATUS")
        requested_datetime = datetime_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_DATETIME"))

        if requested_datetime is None:
            return None

        request_subject = get_xml_val(xml, "./REQUEST/SUBJECT")
        request_detail = get_xml_val(xml, "./REQUEST/BODY")
        requested_by_id = int_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_BY_WUA_ID"))
        email_cc_address_list_str = get_xml_val(xml, "./REQUEST/CC_EMAIL_LIST")
        response_detail = get_xml_val(xml, "./RESPONSE/RESPONSE_DETAILS")
        response_datetime = datetime_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_DATETIME"))
        response_by_id = int_or_none(get_xml_val(xml, "./RESPONSE/RESPONDED_BY_WUA_ID"))
        closed_datetime = datetime_or_none(get_xml_val(xml, "./CLOSE/CLOSED_DATETIME"))
        closed_by_id = int_or_none(get_xml_val(xml, "./CLOSE/CLOSED_BY_WUA_ID"))
        deleted_datetime = datetime_or_none(get_xml_val(xml, "./DELETE/DELETED_DATETIME"))
        deleted_by_id = int_or_none(get_xml_val(xml, "./DELETE/DELETED_BY_WUA_ID"))

        return cls.MODEL(
            **{
                cls.PARENT_MODEL_FIELD: parent_pk,
                "status": status,
                "request_subject": request_subject,
                "request_detail": request_detail,
                "requested_by_id": requested_by_id,
                "requested_datetime": requested_datetime,
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
    def add_process_model(cls, process_pk: int, xml: etree.ElementTree) -> Process:
        status = get_xml_val(xml, "./STATUS")
        created = datetime_or_none(get_xml_val(xml, "./REQUEST/REQUESTED_DATETIME"))

        return Process(
            id=process_pk,
            process_type="FurtherInformationRequest",
            is_active=status != "DELETED",
            created=created,
        )
