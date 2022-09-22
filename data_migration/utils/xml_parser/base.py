from collections import defaultdict
from typing import Generator, Optional, Type, Union

from django.db.models import Model, QuerySet
from lxml import etree

from data_migration.management.commands.utils.db import new_process_pk
from data_migration.models.flow import Process

BatchT = list[tuple]
ModelListT = dict[Type[Model], list[Model]]


class BaseXmlParser:
    # The name of the node which the object data can be found
    ROOT_NODE: str = ""

    # The model to be populated by the parser
    MODEL: Optional[Type[Model]] = None

    # The model or list of models in which the xml data stored
    PARENT: Union[list[Type[Model]], Optional[Type[Model]]] = None

    # The name of the field the xml data is stored under
    FIELD: str = ""

    IS_PROCESS: bool = False

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
            return QuerySet.union(*querysets).iterator()

        return (
            cls.PARENT.objects.filter(**{f"{cls.FIELD}__isnull": False})
            .values_list("pk", cls.FIELD)
            .iterator()
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
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[Model]:
        """Retrieves data for fields from an ElementTree object

        :param parent_pk: The pk of the parent model
        :param xml: An xml tree from which the data for the model will be extracted
        """
        raise NotImplementedError("XML parsing must be defined")

    @classmethod
    def log_message(cls, idx: int) -> str:
        return f"{idx} - Running {cls.__name__}"
