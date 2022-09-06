from typing import TYPE_CHECKING, Optional

from data_migration import models as dm
from data_migration.utils.format import get_xml_val, int_or_none, xml_str_or_none

from .base import BaseXmlParser

if TYPE_CHECKING:
    from lxml.etree import ElementTree as ET


class CFSProductParser(BaseXmlParser):
    MODEL = dm.CFSProduct
    PARENT = dm.CFSSchedule
    FIELD = "product_xml"
    ROOT_NODE = "/PRODUCT_LIST/PRODUCT"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> Optional[dm.CFSProduct]:
        """Example XML structure

        <PRODUCT>
          <NAME />
          <PRODUCT_TYPE_NUMBER_LIST />
          <ACTIVE_INGREDIENT_LIST />
          <CHEMICAL_NAME />
          <MANUFACTURING_PROCESS />
          <IS_BIOCIDAL_FLAG />
        </PRODUCT>
        """

        name = get_xml_val(xml, "./NAME")

        if not name:
            return None

        active_ingredient_xml = get_xml_val(xml, "./ACTIVE_INGREDIENT_LIST", text=False)
        product_type_xml = get_xml_val(xml, "./PRODUCT_TYPE_NUMBER_LIST", text=False)

        return cls.MODEL(
            **{
                "schedule_id": parent_pk,
                "product_name": name,
                "active_ingredient_xml": xml_str_or_none(active_ingredient_xml),
                "product_type_xml": xml_str_or_none(product_type_xml),
            }
        )


class ActiveIngredientParser(BaseXmlParser):
    MODEL = dm.CFSProductActiveIngredient
    PARENT = dm.CFSProduct
    FIELD = "active_ingredient_xml"
    ROOT_NODE = "/ACTIVE_INGREDIENT_LIST/ACTIVE_INGREDIENT"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> Optional[dm.CFSProductActiveIngredient]:
        """Example XML structure

        <ACTIVE_INGREDIENT>
          <NAME />
          <CAS_NUMBER />
          <ACTIONS />
        </ACTIVE_INGREDIENT>
        """

        name = get_xml_val(xml, "./NAME")
        cas_number = get_xml_val(xml, "./CAS_NUMBER")

        if not name or not cas_number:
            return None

        return cls.MODEL(
            **{
                "product_id": parent_pk,
                "name": name,
                "cas_number": cas_number,
            }
        )


class ProductTypeParser(BaseXmlParser):
    MODEL = dm.CFSProductType
    PARENT = dm.CFSProduct
    FIELD = "product_type_xml"
    ROOT_NODE = "/PRODUCT_TYPE_NUMBER_LIST/PRODUCT_TYPE_NUMBER"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> Optional[dm.CFSProductType]:
        """Example XML structure

        <PRODUCT_TYPE_NUMBER>
          <NUMBER />
          <ACTIONS />
        </PRODUCT_TYPE_NUMBER>
        """

        number = int_or_none(get_xml_val(xml, "./NUMBER"))

        if not number:
            return None

        return cls.MODEL(
            **{
                "product_id": parent_pk,
                "product_type_number": number,
            }
        )


class CFSLegislationParser(BaseXmlParser):
    MODEL = dm.CFSLegislation
    PARENT = dm.CFSSchedule
    FIELD = "legislation_xml"
    ROOT_NODE = "/LEGISLATION_LIST/LEGISLATION"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> Optional[dm.CFSLegislation]:
        """Example XML structure

        <LEGISLATION_LIST>
          <LEGISLATION />
        </LEGISLATION_LIST>
        """

        legislation = int_or_none(get_xml_val(xml, "."))

        if not legislation:
            return None

        return cls.MODEL(
            **{
                "cfsschedule_id": parent_pk,
                "productlegislation_id": legislation,
            }
        )
