from django.db.models import Model
from lxml import etree

from data_migration import models as dm
from data_migration.utils.format import (
    get_xml_val,
    int_or_none,
    str_to_yes_no,
    xml_str_or_none,
)

from .base import BaseXmlParser
from .export_application import (
    ActiveIngredientParser,
    CFSLegislationParser,
    CFSProductParser,
    ProductTypeParser,
)


class CATTemplateCountryParser(BaseXmlParser):
    PARENT: Model
    MODEL: Model
    FIELD = "countries_xml"
    ROOT_NODE = "/COUNTRIES/COUNTRY_LIST/COUNTRY"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <COUNTRY_LIST>
          <COUNTRY />
        </COUNTRY_LIST>
        """
        country_id = int_or_none(get_xml_val(xml, "."))

        if not country_id:
            return None

        return cls.MODEL(
            **{
                "country_id": country_id,
                f"{cls.PARENT.__name__.lower()}_id": parent_pk,
            }
        )


class CFSApplicationTemplateCountryParser(CATTemplateCountryParser):
    MODEL = dm.CFSTemplateCountries
    PARENT = dm.CertificateOfFreeSaleApplicationTemplate


class COMApplicationTemplateCountryParser(CATTemplateCountryParser):
    MODEL = dm.COMTemplateCountries
    PARENT = dm.CertificateOfManufactureApplicationTemplate


class CFSScheduleTemplateParser(BaseXmlParser):
    MODEL = dm.CFSScheduleTemplate
    PARENT = dm.CertificateOfFreeSaleApplicationTemplate
    FIELD = "schedules_xml"
    ROOT_NODE = "/SCHEDULE_LIST/SCHEDULE"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Model | None:
        """Example XML

        <SCHEDULE_LIST>
          <SCHEDULE>
            <IS_DOMESTIC_MARKET_PESTICIDE />
            <IS_PESTICIDE_MANUFACTURER />
            <MANUFACTURER_STATUS />
            <BRAND_NAME_STATUS />
            <LEGISLATION_LIST />
              <LEGISLATION />
            </LEGISLATION_LIST>
            <BIOCIDAL_CLAIMS />
            <ELIGIBILITY />
            <IS_EU_MARKET />
            <IS_NEVER_EU_MARKET/>
            <RAW_MATERIALS_EXIST />
            <END_USE />
            <COUNTRY_OF_MANUFACTURE />
            <STATEMENT_LIST>
              <STATEMENT />
            </STATEMENT_LIST>
            <MANUFACTURED_AT>
              <INCLUDE_ON_SCHEDULE />
              <NAME />
              <ADDRESS_ENTRY_TYPE />
              <POSTCODE />
              <ADDRESS />
            </MANUFACTURED_AT>
            <CFS_TEMPLATE />
            <CFS_UPLOADER />
            <PRODUCT_LIST />
          </SCHEUDLE
        </SCHEDULE_LIST>
        """
        exporter_status = get_xml_val(xml, "./MANUFACTURER_STATUS")
        exporter_status = exporter_status and exporter_status.lstrip("IS_")
        brand_name_holder = str_to_yes_no(get_xml_val(xml, "./BRAND_NAME_STATUS"))
        biocidal_claim = str_to_yes_no(get_xml_val(xml, "./BIOCIDAL_CLAIMS"))
        eligibility = {"ON_SALE": "SOLD_ON_UK_MARKET", "MAY_BE_SOLD": "MEET_UK_PRODUCT_SAFETY"}
        product_eligibility = eligibility.get(get_xml_val(xml, "./ELIGIBILITY"))
        goods_placed_on_uk_market = str_to_yes_no(get_xml_val(xml, "./IS_NEVER_EU_MARKET"))
        goods_export_only = str_to_yes_no(get_xml_val(xml, "./IS_EU_MARKET"))
        any_raw_materials = str_to_yes_no(get_xml_val(xml, "./RAW_MATERIALS_EXIST"))
        final_product_end_use = get_xml_val(xml, "./END_USE")
        country_of_manufacture = int_or_none(get_xml_val(xml, "./COUNTRY_OF_MANUFACTURE"))
        statements = [
            get_xml_val(statement, ".")
            for statement in get_xml_val(xml, "./STATEMENT_LIST", text=False)
        ]
        statements_standards = (
            "GOOD_MANUFACTURING_PRACTICE" in statements
            or "GOOD_MANUFACTURING_PRACTICE_NI" in statements
        )
        statements_responsible_person = (
            "EU_COSMETICS_RESPONSIBLE_PERSON" in statements
            or "EU_COSMETICS_RESPONSIBLE_PERSON" in statements
        )
        manufacturer_name = get_xml_val(xml, "./MANUFACTURED_AT/NAME")
        manufacturer_address_entry_type = get_xml_val(xml, "./MANUFACTURED_AT/ADDRESS_ENTRY_TYPE")
        manufacturer_postcode = get_xml_val(xml, "./MANUFACTURED_AT/POSTCODE")
        manufacturer_address = get_xml_val(xml, "./MANUFACTURED_AT/ADDRESS")
        product_xml = get_xml_val(xml, "./PRODUCT_LIST", text=False)
        legislation_xml = get_xml_val(xml, "./LEGISLATION_LIST", text=False)

        return cls.MODEL(
            **{
                "application_id": parent_pk,
                "exporter_status": exporter_status,
                "brand_name_holder": brand_name_holder,
                "biocidal_claim": biocidal_claim,
                "product_eligibility": product_eligibility,
                "goods_placed_on_uk_market": goods_placed_on_uk_market,
                "goods_export_only": goods_export_only,
                "any_raw_materials": any_raw_materials,
                "final_product_end_use": final_product_end_use,
                "country_of_manufacture_id": country_of_manufacture,
                "schedule_statements_accordance_with_standards": statements_standards,
                "schedule_statements_is_responsible_person": statements_responsible_person,
                "manufacturer_name": manufacturer_name,
                "manufacturer_address_entry_type": manufacturer_address_entry_type or "MANUAL",
                "manufacturer_postcode": manufacturer_postcode,
                "manufacturer_address": manufacturer_address,
                "product_xml": xml_str_or_none(product_xml),
                "legislation_xml": xml_str_or_none(legislation_xml),
            }
        )


class CFSTemplateProductParser(CFSProductParser):
    MODEL = dm.CFSProductTemplate
    PARENT = dm.CFSScheduleTemplate


class CFSTemplateProductTypeParser(ProductTypeParser):
    MODEL = dm.CFSProductTypeTemplate
    PARENT = dm.CFSProductTemplate


class CFSTemplateActiveIngredientParser(ActiveIngredientParser):
    MODEL = dm.CFSProductActiveIngredientTemplate
    PARENT = dm.CFSProductTemplate


class CFSTemplateLegislationParser(CFSLegislationParser):
    MODEL = dm.CFSTemplateLegislation
    PARENT = dm.CFSScheduleTemplate
