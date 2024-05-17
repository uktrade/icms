import re
from collections import defaultdict
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Optional

from django.utils import timezone
from lxml import etree

from data_migration import models as dm
from data_migration.utils.format import (
    date_or_none,
    decimal_or_none,
    get_xml_val,
    int_or_none,
    str_to_bool,
    str_to_yes_no,
    xml_str_or_none,
)

from .base import BaseXmlParser, BatchT, ModelListT

if TYPE_CHECKING:
    from django.db.models import Model
    from lxml.etree import ElementTree as ET

FA_TYPE_CODES = {
    "DEACTIVATED": "deactivated",
    "RFD": "registered",
    "SHOTGUN": "shotgun",
    "FIREARMS": "firearms",
}


def get_goods_item_position_from_xml(goods_xml: "ET") -> int:
    """The goods item position is the order in which the goods appear in the COMMODITY_LIST.
    GOODS_ITEM_ID is GOODS_ITEM_DESC and goods item position concatenated together.
    This function retrieves the goods item position from the GOODS_ITEM_ID node.
    """

    goods_item_desc = get_xml_val(goods_xml, "GOODS_ITEM_DESC")
    good_item_id = get_xml_val(goods_xml, "GOOD_ITEM_ID")
    return get_goods_item_position_from_description(good_item_id, goods_item_desc)


def get_goods_item_position_from_description(good_item_id: str, goods_item_desc: str) -> int:
    string_suffix = good_item_id.replace(goods_item_desc, "")
    numbers = re.findall(r"\d+", string_suffix)
    return int(numbers[-1])


class ImportContactParser(BaseXmlParser):
    MODEL = dm.ImportContact
    PARENT = [dm.SILApplication, dm.OpenIndividualLicenceApplication, dm.DFLApplication]
    FIELD = "bought_from_details_xml"
    ROOT_NODE = "/SELLER_HOLDER_LIST/SELLER_HOLDER"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.ImportContact:
        """Example XML structure

        <SELLER_HOLDER>
          <PERSON_DETAILS>
            <PERSON_TYPE />
            <LEGAL_PERSON_NAME />
            <REGISTRATION_NUMBER />
            <FIRST_NAME />
            <SURNAME />
          </PERSON_DETAILS>
          <ADDRESS>
            <STREET_AND_NUMBER />
            <TOWN_CITY />
            <POSTCODE />
            <REGION />
            <COUNTRY />
          </ADDRESS>
          <IS_DEALER_FLAG />
          <SELLER_HOLDER_ID />
          <UPDATE_FLAG />
        </SELLER_HOLDER>
        """

        legacy_id = get_xml_val(xml, "./SELLER_HOLDER_ID")
        entity = get_xml_val(xml, "./PERSON_DETAILS/PERSON_TYPE")
        entity = entity.lower().removesuffix("_person")
        if entity == "legal":
            first_name = get_xml_val(xml, "./PERSON_DETAILS/LEGAL_PERSON_NAME")
        else:
            first_name = get_xml_val(xml, "./PERSON_DETAILS/FIRST_NAME")
        last_name = get_xml_val(xml, "./PERSON_DETAILS/SURNAME")
        registration_number = get_xml_val(xml, "./PERSON_DETAILS/REGISTRATION_NUMBER")
        street = get_xml_val(xml, "./ADDRESS/STREET_AND_NUMBER")
        city = get_xml_val(xml, "./ADDRESS/TOWN_CITY")
        postcode = get_xml_val(xml, "./ADDRESS/POSTCODE")
        region = get_xml_val(xml, "./ADDRESS/REGION")
        dealer = get_xml_val(xml, "./IS_DEALER_FLAG")
        country_id = get_xml_val(xml, "./ADDRESS/COUNTRY")

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "legacy_id": legacy_id,
                "entity": entity,
                "first_name": first_name,
                "last_name": last_name,
                "registration_number": registration_number,
                "street": street,
                "city": city,
                "postcode": postcode,
                "region": region,
                "dealer": str_to_yes_no(dealer),
                "country_id": country_id,
                "created_datetime": timezone.now(),
            }
        )


class UserImportCertificateParser(BaseXmlParser):
    MODEL = dm.UserImportCertificate
    PARENT = [dm.SILApplication, dm.OpenIndividualLicenceApplication]
    FIELD = "user_import_certs_xml"
    ROOT_NODE = "/FIREARMS_CERTIFICATE_LIST/FIREARMS_CERTIFICATE"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.UserImportCertificate | None:
        """Example XML structure

        <FIREARMS_CERTIFICATE>
          <TARGET_ID />
          <CERTIFICATE_REF />
          <CERTIFICATE_TYPE />
          <CONSTABULARY />
          <DATE_ISSUED />
          <EXPIRY_DATE />
          <ISSUING_COUNTRY />
        </FIREARMS_CERTIFICATE>
        """
        target_id = get_xml_val(xml, "./TARGET_ID")
        certificate_type = get_xml_val(xml, "./CERTIFICATE_TYPE")

        if not target_id or not certificate_type:
            # There needs to be an file and certificate_type associated with the data
            return None

        reference = get_xml_val(xml, "./CERTIFICATE_REF")
        constabulary_id = get_xml_val(xml, "./CONSTABULARY")
        date_issued = get_xml_val(xml, "./DATE_ISSUED")
        expiry_date = get_xml_val(xml, "./EXPIRY_DATE")

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "target_id": target_id,
                "reference": reference,
                "certificate_type": FA_TYPE_CODES[certificate_type],
                "constabulary_id": constabulary_id,
                "date_issued": date_or_none(date_issued),
                "expiry_date": date_or_none(expiry_date),
            }
        )


class SILGoodsParser(BaseXmlParser):
    PARENT = dm.SILApplication
    FIELD = "commodities_xml"
    ROOT_NODE = "/COMMODITY_LIST/COMMODITY"

    @classmethod
    def parse_xml(cls, batch: BatchT) -> ModelListT:
        """
        <COMMODITY_LIST>
          <COMMODITY />
        </COMMODITY_LIST>
        """
        model_lists: ModelListT = defaultdict(list)

        for parent_pk, xml_str in batch:
            xml_tree = etree.fromstring(xml_str)

            commodity_list = xml_tree.xpath(cls.ROOT_NODE)

            for i, xml in enumerate(commodity_list, start=1):
                section = get_xml_val(xml, "./SECTION")

                if not section:
                    commodity_desc = get_xml_val(xml, "./COMMODITY_DESC")

                    if not commodity_desc:
                        continue

                    # If there is a commodity description this is an older record with no section
                    section = "LEGACY"

                obj = cls.parse_xml_fields(parent_pk, xml)

                if not obj:
                    continue

                obj.legacy_ordinal = i
                model_lists[obj._meta.model].append(obj)

                # Populate the SILSection model so we know which section model to retrieve the goods info
                sil_section = dm.SILSection(
                    **{
                        "section": section,
                        "legacy_ordinal": i,
                        "import_application_id": parent_pk,
                    }
                )
                model_lists[dm.SILSection].append(sil_section)

        return model_lists

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        """
        <COMMODITY>
          <SECTION />
          <SECTION_5_CLAUSE />
          <COMMODITY_DESC />
          <OBSOLETE_CALIBRE />
          <QUANTITY />
          <QUANTITY_UNLIMITED />
          <QUANTITY_UNLIMITED_FLAG />
          <MANUFACTURED_BEFORE_1900 />
          <CURIOSITY_OR_ORNAMENT />
          <CURIOSITY_STATEMENT_AGREED />
          <BREECH_LOADING_CENTREFIRE />
          <MANUFACTURED_AFTER_1899_BEFORE_1939 />
          <ORIGINAL_CHAMBERING />
          <MUZZLE_LOADING />
          <OTHER_BREECH_RIMFIRE_CARTRIDGE />
          <OTHER_BREECH_RIMFIRE_CARTRIDGE_SPECIFIED />
          <OTHER_IGNITION_SYSTEM />
          <OTHER_IGNITION_SYSTEM_SPECIFIED />
          <OTHER_IGNITION_SYSTEM_SPECIFIED_OTHER />
          <SHOTGUN_PUNTGUN_RIFLE_LISTED_CARTRIDGES />
          <SHOTGUN_PUNTGUN_RIFLE_OVER_10_BORE />
          <SHOTGUN_PUNTGUN_RIFLE_OVER_10_BORE_SPECIFIED />
          <OTHER_OPTIONS_ERROR />
          <S58_2_YES_ANSWER_COUNT />
          <OBSOLETE_CALIBRE_SELECTED />
        </COMMODITY>
        """

        section = get_xml_val(xml, "./SECTION") or "LEGACY"
        return getattr(cls, f"parse_{section.lower()}")(parent_pk, xml)

    @classmethod
    def parse_sec_base(cls, parent_pk: int, xml: etree.ElementTree) -> dict[str, Any]:
        description = get_xml_val(xml, "./COMMODITY_DESC")
        manufacture = get_xml_val(xml, "./MANUFACTURED_BEFORE_1900")
        quantity = get_xml_val(xml, "./QUANTITY")

        return {
            "import_application_id": parent_pk,
            "description": description,
            "manufacture": str_to_bool(manufacture),
            "quantity": int_or_none(quantity),
        }

    @classmethod
    def parse_sec1(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)
        unlimited_quantity = get_xml_val(xml, "./QUANTITY_UNLIMITED_FLAG")

        return dm.SILGoodsSection1(
            **data | {"unlimited_quantity": bool(str_to_bool(unlimited_quantity))}
        )

    @classmethod
    def parse_sec2(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)
        unlimited_quantity = get_xml_val(xml, "./QUANTITY_UNLIMITED_FLAG")

        return dm.SILGoodsSection2(
            **data | {"unlimited_quantity": bool(str_to_bool(unlimited_quantity))}
        )

    @classmethod
    def parse_sec5(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)
        section_5_clause = get_xml_val(xml, "./SECTION_5_CLAUSE")
        unlimited_quantity = get_xml_val(xml, "./QUANTITY_UNLIMITED_FLAG")

        return dm.SILGoodsSection5(
            **data
            | {
                "section_5_clause_id": section_5_clause,
                "unlimited_quantity": bool(str_to_bool(unlimited_quantity)),
            }
        )

    @classmethod
    def parse_obsolete_calibre(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)
        acknowledgement = get_xml_val(xml, "./CURIOSITY_STATEMENT_AGREED")
        centrefire = get_xml_val(xml, "./BREECH_LOADING_CENTREFIRE")
        curiosity_ornament = get_xml_val(xml, "./CURIOSITY_OR_ORNAMENT")
        manufacture = get_xml_val(xml, "./MANUFACTURED_AFTER_1899_BEFORE_1939")
        obsolete_calibre = get_xml_val(xml, "./OBSOLETE_CALIBRE/OC_ID")
        original_chambering = get_xml_val(xml, "./ORIGINAL_CHAMBERING")

        return dm.SILGoodsSection582Obsolete(  # /PS-IGNORE
            **data
            | {
                "acknowledgement": str_to_bool(acknowledgement),
                "centrefire": str_to_bool(centrefire),
                "curiosity_ornament": str_to_bool(curiosity_ornament),
                "manufacture": str_to_bool(manufacture),
                "obsolete_calibre_legacy_id": int_or_none(obsolete_calibre),
                "original_chambering": str_to_bool(original_chambering),
            }
        )

    @classmethod
    def parse_other(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)

        acknowledgement = get_xml_val(xml, "./CURIOSITY_STATEMENT_AGREED")
        bore = get_xml_val(xml, "./SHOTGUN_PUNTGUN_RIFLE_OVER_10_BORE")
        bore_details = get_xml_val(xml, "./SHOTGUN_PUNTGUN_RIFLE_OVER_10_BORE_SPECIFIED")
        chamber = get_xml_val(xml, "./SHOTGUN_PUNTGUN_RIFLE_LISTED_CARTRIDGES")
        curiosity_ornament = get_xml_val(xml, "./CURIOSITY_OR_ORNAMENT")
        ignition = get_xml_val(xml, "./OTHER_IGNITION_SYSTEM")
        ignition_details = get_xml_val(xml, "./OTHER_IGNITION_SYSTEM_SPECIFIED")
        ignition_other = get_xml_val(xml, "./OTHER_IGNITION_SYSTEM_SPECIFIED_OTHER")
        manufacture = get_xml_val(xml, "./MANUFACTURED_AFTER_1899_BEFORE_1939")
        muzzle_loading = get_xml_val(xml, "./MUZZLE_LOADING")
        rimfire = get_xml_val(xml, "./OTHER_BREECH_RIMFIRE_CARTRIDGE")
        rimfire_details = get_xml_val(xml, "./OTHER_BREECH_RIMFIRE_CARTRIDGE_SPECIFIED")

        return dm.SILGoodsSection582Other(  # /PS-IGNORE
            **data
            | {
                "acknowledgement": str_to_bool(acknowledgement),
                "bore": str_to_bool(bore),
                "bore_details": bore_details or "",
                "chamber": str_to_bool(chamber),
                "curiosity_ornament": str_to_bool(curiosity_ornament),
                "ignition": str_to_bool(ignition),
                "ignition_details": ignition_details or "",
                "ignition_other": ignition_other or "",
                "manufacture": str_to_bool(manufacture),
                "muzzle_loading": str_to_bool(muzzle_loading),
                "rimfire": str_to_bool(rimfire),
                "rimfire_details": rimfire_details or "",
            }
        )

    @classmethod
    def parse_legacy(cls, parent_pk: int, xml: "ET") -> Optional["Model"]:
        """Example XML

        <COMMODITY>
          <COMMODITY_DESC />
          <QUANTITY />
          <QUANTITY_UNLIMITED />
          <QUANTITY_UNLIMITED_FLAG />
          <UNIT />
          <OBSOLETE_CALIBRE>
            <OC_ID />
            <OC_ID_ERROR />
            <NA_FLAG />
          </OBSOLETE_CALIBRE>
        </COMMODITY>
        """

        description = get_xml_val(xml, "./COMMODITY_DESC")
        quantity = get_xml_val(xml, "./QUANTITY")
        unlimited_quantity = get_xml_val(xml, "./QUANTITY_UNLIMITED_FLAG")
        obsolete_calibre = get_xml_val(xml, "./OBSOLETE_CALIBRE/OC_ID")

        return dm.SILLegacyGoods(
            **{
                "import_application_id": parent_pk,
                "description": description,
                "quantity": int_or_none(quantity),
                "unlimited_quantity": bool(str_to_bool(unlimited_quantity)),
                "obsolete_calibre_legacy_id": int_or_none(obsolete_calibre),
            }
        )


class SupplementaryReportParser(BaseXmlParser):
    FIELD = "supplementary_report_xml"
    ROOT_NODE = (
        "/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT/FA_SUPPLEMENTARY_REPORT_DETAILS"
    )

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.SupplementaryReportBase:
        """Example XML structure

        <FA_SUPPLEMENTARY_REPORT>
          <HISTORICAL_REPORT_LIST />
          <FA_SUPPLEMENTARY_REPORT_DETAILS>
            <GOODS_LINE_LIST />
            <MODE_OF_TRANSPORT />
            <RECEIVED_DATE />
            <REPORT_SELLER_HOLDER />
            <REPORT_SUBMITTED_FLAG />
            <SUBMITTED_BY_WUA_ID />
            <SUBMITTED_DATETIME />
            <FA_REPORT_ID />
          </FA_SUPPLEMENTARY_REPORT_DETAILS>
        </FA_SUPPLEMENTARY_REPORT>
        """

        if not cls.MODEL:
            raise NotImplementedError("MODEL must be defined on the class")

        transport = get_xml_val(xml, "./MODE_OF_TRANSPORT[not(fox-error)]")
        date_received = get_xml_val(xml, "./RECEIVED_DATE[not(fox-error)]")
        report_firearms_xml = get_xml_val(xml, "./GOODS_LINE_LIST", text=False)
        bought_from_legacy_id = get_xml_val(xml, "./REPORT_SELLER_HOLDER[not(fox-error)]")

        return cls.MODEL(
            **{
                "supplementary_info_id": parent_pk,
                "transport": transport,
                "date_received": date_or_none(date_received),
                "bought_from_legacy_id": bought_from_legacy_id,
                "report_firearms_xml": xml_str_or_none(report_firearms_xml),
            }
        )


class DFLSupplementaryReportParser(SupplementaryReportParser):
    MODEL = dm.DFLSupplementaryReport
    PARENT = dm.DFLSupplementaryInfo


class OILSupplementaryReportParser(SupplementaryReportParser):
    MODEL = dm.OILSupplementaryReport
    PARENT = dm.OILSupplementaryInfo


class SILSupplementaryReportParser(SupplementaryReportParser):
    MODEL = dm.SILSupplementaryReport
    PARENT = dm.SILSupplementaryInfo


class ReportFirearmParser(BaseXmlParser):
    FIELD = "report_firearms_xml"
    ROOT_NODE = "/GOODS_LINE_LIST/GOODS_LINE"

    @classmethod
    def parse_xml(cls, batch: BatchT) -> ModelListT:
        """Example XML structure

        <GOODS_LINE_LIST>
          <GOODS_LINE>
            <FA_REPORTING_MODE />
            <FIREARMS_DETAILS_LIST>
              <FIREARMS_DETAILS />
            </FIREARMS_DETAILS_LIST>
            <FILE_UPLOAD_LIST>
              <FILE_UPLOAD>
                <FILE_CONTENT>
                    <filename />
                    <file-id />
                    <content-type />
                    <upload-date-time />
                </FILE_CONTENT>
              </FILE_UPLOAD>
            </FILE_UPLOAD_LIST>
          </GOODS_LINE>
        </GOODS_LINE_LIST>
        """

        if not cls.MODEL:
            raise NotImplementedError("MODEL must be defined on the class")

        model_list: ModelListT = defaultdict(list)
        for parent_pk, xml in batch:
            xml_tree = etree.fromstring(xml)
            goods_xml_list = xml_tree.xpath(cls.ROOT_NODE)

            for goods_xml in goods_xml_list:
                reporting_mode = get_xml_val(goods_xml, "./FA_REPORTING_MODE")
                firearm_details_xml_list = goods_xml.xpath(
                    "./FIREARMS_DETAILS_LIST/FIREARMS_DETAILS"
                )
                ordinal = get_goods_item_position_from_xml(goods_xml)
                # reporting mode only accurate for upload. MANUAL and NO_REPORT both contain null values
                if reporting_mode == "UPLOAD":
                    upload_xml_list = goods_xml.xpath("./FILE_UPLOAD_LIST/FILE_UPLOAD")
                    for upload_xml in upload_xml_list:
                        file_id = get_xml_val(upload_xml, "./FILE_CONTENT/file-id")
                        model_list[cls.MODEL].append(
                            cls.MODEL(
                                report_id=parent_pk,
                                is_upload=True,
                                goods_certificate_legacy_id=ordinal,
                                file_id=file_id,
                            )
                        )

                # handle manually entered goods data
                elif firearm_details_xml_list:
                    for firearm_xml in firearm_details_xml_list:
                        obj = cls.parse_manual_xml(parent_pk, firearm_xml)
                        obj.goods_certificate_legacy_id = ordinal
                        model_list[obj._meta.model].append(obj)

                # no firearm reported
                else:
                    model_list[cls.MODEL].append(
                        cls.MODEL(
                            report_id=parent_pk,
                            is_no_firearm=True,
                            goods_certificate_legacy_id=ordinal,
                        )
                    )

        return model_list

    @classmethod
    def parse_manual_xml(cls, parent_pk: int, xml: "ET") -> "Model":
        """Exmaple XML structure

        <FIREARMS_DETAILS>
          <SERIAL_NUMBER />
          <CALIBRE />
          <MAKE_MODEL />
          <PROOFING />
        </FIREARMS_DETAILS>
        """

        if not cls.MODEL:
            raise NotImplementedError("MODEL must be defined on the class")

        serial_number = get_xml_val(xml, "./SERIAL_NUMBER")
        calibre = get_xml_val(xml, "./CALIBRE")
        model = get_xml_val(xml, "./MAKE_MODEL")
        proofing = get_xml_val(xml, "./PROOFING")

        return cls.MODEL(
            **{
                "report_id": parent_pk,
                "serial_number": serial_number,
                "calibre": calibre,
                "model": model,
                "proofing": str_to_yes_no(proofing),
                "is_manual": True,
            }
        )


class DFLReportFirearmParser(ReportFirearmParser):
    MODEL = dm.DFLSupplementaryReportFirearm
    PARENT = dm.DFLSupplementaryReport


class OILReportFirearmParser(ReportFirearmParser):
    MODEL = dm.OILSupplementaryReportFirearm
    PARENT = dm.OILSupplementaryReport


class SILReportFirearmParser(BaseXmlParser):
    ROOT_NODE = "/GOODS_LINE_LIST/GOODS_LINE"
    SECTION_MODEL = {
        "SEC1": dm.SILSupplementaryReportFirearmSection1,
        "SEC2": dm.SILSupplementaryReportFirearmSection2,
        "SEC5": dm.SILSupplementaryReportFirearmSection5,
        "OBSOLETE_CALIBRE": dm.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
        "OTHER": dm.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        "LEGACY": dm.SILSupplementaryReportFirearmSectionLegacy,
    }

    @classmethod
    def sort_goods_list_xml(cls, goods_list_xml: list["ET"]) -> dict[int, "ET"]:
        goods_xml_dict: dict[int, "ET"] = {}
        for goods_xml in goods_list_xml:
            goods_item_position = get_goods_item_position_from_xml(goods_xml)
            goods_xml_dict[goods_item_position] = goods_xml
        return goods_xml_dict

    @classmethod
    def get_queryset(cls) -> Generator:
        supplementary_info = "import_application__imad__supplementary_info"
        reports = f"{supplementary_info}__reports"
        xml_field = f"{reports}__report_firearms_xml"

        return (
            dm.SILSection.objects.select_related(supplementary_info)
            .prefetch_related(reports)
            .filter(**{f"{xml_field}__isnull": False})
            .values_list(f"{reports}__pk", xml_field, "section", "legacy_ordinal")
            .iterator(chunk_size=2000)
        )

    @classmethod
    def parse_xml(cls, batch: BatchT) -> ModelListT:
        """Example XML structure

        <GOODS_LINE_LIST>
          <GOODS_LINE>
            <FA_REPORTING_MODE />
            <FIREARMS_DETAILS_LIST>
              <FIREARMS_DETAILS />
            </FIREARMS_DETAILS_LIST>
            <FILE_UPLOAD_LIST>
              <FILE_UPLOAD>
                <FILE_CONTENT>
                    <filename />
                    <file-id />
                    <content-type />
                    <upload-date-time />
                </FILE_CONTENT>
              </FILE_UPLOAD>
            </FILE_UPLOAD_LIST>
          </GOODS_LINE>
        </GOODS_LINE_LIST>
        """

        model_list: ModelListT = defaultdict(list)

        for parent_pk, xml, section, ordinal in batch:
            xml_tree = etree.fromstring(xml)
            goods_xml_list = xml_tree.xpath(cls.ROOT_NODE)
            goods_xml_dict = cls.sort_goods_list_xml(goods_xml_list)
            goods_xml = goods_xml_dict[ordinal]
            reporting_mode = get_xml_val(goods_xml, "./FA_REPORTING_MODE")
            firearm_details_xml_list = goods_xml.xpath("./FIREARMS_DETAILS_LIST/FIREARMS_DETAILS")
            model = cls.SECTION_MODEL[section]

            # reporting mode only accurate for upload. MANUAL and NO_REPORT both contain null values
            if reporting_mode == "UPLOAD":
                upload_xml_list = goods_xml.xpath("./FILE_UPLOAD_LIST/FILE_UPLOAD")
                for upload_xml in upload_xml_list:
                    file_id = get_xml_val(upload_xml, "./FILE_CONTENT/file-id")
                    model_list[model].append(
                        model(
                            report_id=parent_pk,
                            is_upload=True,
                            goods_certificate_legacy_id=ordinal,
                            file_id=file_id,
                        )
                    )

            # handle manually entered goods data
            elif firearm_details_xml_list:
                for firearm_details_xml in firearm_details_xml_list:
                    obj = cls.parse_manual_xml(parent_pk, model, firearm_details_xml)
                    obj.goods_certificate_legacy_id = ordinal
                    model_list[model].append(obj)

            # no firearms reported
            else:
                model_list[model].append(
                    model(
                        report_id=parent_pk,
                        is_no_firearm=True,
                        goods_certificate_legacy_id=ordinal,
                    )
                )

        return model_list

    @classmethod
    def parse_manual_xml(cls, parent_pk: int, goods_model: "Model", xml: "ET") -> "Model":
        """Exmaple XML structure

        <FIREARMS_DETAILS>
          <SERIAL_NUMBER />
          <CALIBRE />
          <MAKE_MODEL />
          <PROOFING />
        </FIREARMS_DETAILS>
        """

        serial_number = get_xml_val(xml, "./SERIAL_NUMBER")
        calibre = get_xml_val(xml, "./CALIBRE")
        model = get_xml_val(xml, "./MAKE_MODEL")
        proofing = get_xml_val(xml, "./PROOFING")

        return goods_model(
            **{
                "report_id": parent_pk,
                "serial_number": serial_number,
                "calibre": calibre,
                "model": model,
                "proofing": str_to_yes_no(proofing),
                "is_manual": True,
            }
        )


class DFLGoodsCertificateParser(BaseXmlParser):
    MODEL = dm.DFLGoodsCertificate
    PARENT = dm.DFLApplication
    FIELD = "fa_goods_certs_xml"

    @classmethod
    def parse_xml(cls, batch: BatchT) -> ModelListT:
        """Example XML

        <FA_GOODS_CERTS>
          <COMMODITY_LIST>
            <COMMODITY />
          </COMMODITY_LIST>
          <FIREARMS_CERTIFICATE_LIST>
            <FIREARMS_CERTIFICATE />
          </FIREARMS_CERTIFICATE_LIST>
        </FA_GOODS_CERTS>
        """

        model_list: ModelListT = defaultdict(list)

        for parent_pk, xml_str in batch:
            xml_tree = etree.fromstring(xml_str)
            # The XML for this model is spread across two different XML elements.
            # First we get a list of each of the elements
            cert_list = xml_tree.xpath("FIREARMS_CERTIFICATE_LIST/FIREARMS_CERTIFICATE")
            commodity_list = xml_tree.xpath("COMMODITY_LIST/COMMODITY")

            # Zip the elements together, as they are related by their ordinal
            xml_zip = zip(cert_list[::-1], commodity_list[::-1])
            for i, (cert_xml, commodity_xml) in enumerate(xml_zip, start=1):
                # Combine the elements under a single node so we can parse the data for the model
                xml = etree.Element("FA_GOODS_CERT")
                xml.append(cert_xml)
                xml.append(commodity_xml)
                obj = cls.parse_xml_fields(parent_pk, xml)

                if not obj:
                    continue

                # Add the legacy ordinal to the object so it can be referenced later
                # The supplementary reports will use the same ordinal to link to the correct goods
                obj.legacy_ordinal = i
                model_list[obj._meta.model].append(obj)

        return model_list

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.DFLGoodsCertificate:
        """Example XML structure

        <FA_GOODS_CERT>
          <FIREARMS_CERTIFICATE>
            <TARGET_ID />
            <CERTIFICATE_REF />
            <CERTIFICATE_TYPE />
            <CONSTABULARY />
            <DATE_ISSUED />
            <EXPIRY_DATE />
            <ISSUING_COUNTRY />
          </FIREARMS_CERTIFICATE>
          <COMMODITY>
            <COMMODITY_DESC />
            <OBSOLETE_CALIBRE />
            <QUANTITY />
            <QUANTITY_UNLIMITED />
            <QUANTITY_UNLIMITED_FLAG />
            <UNIT />
          </COMMODITY>
        </FA_GOODS_CERT>
        """

        target_id = get_xml_val(xml, "./FIREARMS_CERTIFICATE/TARGET_ID")
        reference = get_xml_val(xml, "./FIREARMS_CERTIFICATE/CERTIFICATE_REF")
        issuing_country = get_xml_val(xml, "./FIREARMS_CERTIFICATE/ISSUING_COUNTRY")
        description = get_xml_val(xml, "./COMMODITY/COMMODITY_DESC")

        return cls.MODEL(
            **{
                "dfl_application_id": parent_pk,
                "target_id": int_or_none(target_id),
                "deactivated_certificate_reference": reference,
                "goods_description": description,
                "issuing_country_id": int_or_none(issuing_country),
            }
        )


class OILApplicationFirearmAuthorityParser(BaseXmlParser):
    MODEL = dm.OILApplicationFirearmAuthority
    PARENT = dm.OpenIndividualLicenceApplication
    FIELD = "fa_authorities_xml"
    ROOT_NODE = "/AUTHORITY_LIST/AUTHORITY"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: "ET"
    ) -> dm.OILApplicationFirearmAuthority | None:
        """Example XML structure

        <AUTHORITY>
          <IA_ID />
          <SELECTED />
        </AUTHORITY>
        """

        ia_id = int_or_none(get_xml_val(xml, "./IA_ID"))
        selected = str_to_bool(get_xml_val(xml, "./SELECTED"))

        if not selected or not ia_id:
            return None

        return cls.MODEL(
            **{"openindividuallicenceapplication_id": parent_pk, "firearmsauthority_id": ia_id}
        )


class SILApplicationFirearmAuthorityParser(BaseXmlParser):
    MODEL = dm.SILApplicationFirearmAuthority
    PARENT = dm.SILApplication
    FIELD = "fa_authorities_xml"
    ROOT_NODE = "/AUTHORITY_LIST/AUTHORITY"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: "ET"
    ) -> dm.SILApplicationFirearmAuthority | None:
        """Example XML structure

        <AUTHORITY>
          <IA_ID />
          <SELECTED />
        </AUTHORITY>
        """

        ia_id = int_or_none(get_xml_val(xml, "./IA_ID"))
        selected = str_to_bool(get_xml_val(xml, "./SELECTED"))

        if not selected or not ia_id:
            return None

        return cls.MODEL(**{"silapplication_id": parent_pk, "firearmsauthority_id": ia_id})


class SILApplicationSection5AuthorityParser(BaseXmlParser):
    MODEL = dm.SILApplicationSection5Authority
    PARENT = dm.SILApplication
    FIELD = "section5_authorities_xml"
    ROOT_NODE = "/AUTHORITY_LIST/AUTHORITY"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: "ET"
    ) -> dm.SILApplicationFirearmAuthority | None:
        """Example XML structure

        <AUTHORITY>
          <IA_ID />
          <SELECTED />
        </AUTHORITY>
        """

        ia_id = int_or_none(get_xml_val(xml, "./IA_ID"))
        selected = str_to_bool(get_xml_val(xml, "./SELECTED"))

        if not selected or not ia_id:
            return None

        return cls.MODEL(**{"silapplication_id": parent_pk, "section5authority_id": ia_id})


class ClauseQuantityParser(BaseXmlParser):
    MODEL = dm.ClauseQuantity
    PARENT = dm.Section5Authority
    FIELD = "clause_quantity_xml"
    ROOT_NODE = "/GOODS_CATEGORY_LIST/GOODS_CATEGORY"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.ClauseQuantity | None:
        """Example XML structure

        <GOODS_CATEGORY>
          <CATEGORY_ID />
          <QUANTITY_WRAPPER>
            <QUANTITY />
            <UNLIMITED_QUANTITY />
          </QUANTITY_WRAPPER>
        </GOODS_CATEGORY>
        """

        clause_id = int_or_none(get_xml_val(xml, "./CATEGORY_ID"))
        quantity = int_or_none(get_xml_val(xml, "./QUANTITY_WRAPPER/QUANTITY"))
        infinity = str_to_bool(get_xml_val(xml, "./QUANTITY_WRAPPER/UNLIMITED_QUANTITY"))

        if not clause_id:
            return None

        if not quantity and not infinity:
            return None

        return cls.MODEL(
            **{
                "section5authority_id": parent_pk,
                "section5clause_id": clause_id,
                "quantity": quantity,
                "infinity": infinity,
            }
        )


class ActQuantityParser(BaseXmlParser):
    MODEL = dm.ActQuantity
    PARENT = dm.FirearmsAuthority
    FIELD = "act_quantity_xml"
    ROOT_NODE = "/GOODS_CATEGORY_LIST/GOODS_CATEGORY"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.ActQuantity | None:
        """Example XML structure

        <GOODS_CATEGORY>
          <CATEGORY_ID />
          <QUANTITY_WRAPPER>
            <QUANTITY />
            <UNLIMITED_QUANTITY />
          </QUANTITY_WRAPPER>
        </GOODS_CATEGORY>
        """

        act_id = int_or_none(get_xml_val(xml, "./CATEGORY_ID"))
        quantity = int_or_none(get_xml_val(xml, "./QUANTITY_WRAPPER/QUANTITY"))
        infinity = str_to_bool(get_xml_val(xml, "./QUANTITY_WRAPPER/UNLIMITED_QUANTITY"))

        if not act_id:
            return None

        if not quantity and not infinity:
            return None

        return cls.MODEL(
            **{
                "firearmsauthority_id": parent_pk,
                "firearmsact_id": act_id,
                "quantity": quantity,
                "infinity": infinity,
            }
        )


class SanctionGoodsParser(BaseXmlParser):
    MODEL = dm.SanctionsAndAdhocApplicationGoods
    PARENT = dm.SanctionsAndAdhocApplication
    FIELD = "commodities_xml"
    ROOT_NODE = "/COMMODITY_LIST/COMMODITY"
    REVERSE_LIST = True

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: "ET"
    ) -> dm.SanctionsAndAdhocApplicationGoods | None:
        """Example XML structure

        <COMMODITY>
          <COMMODITY_ID />
          <COMMODITY_DESC />
          <QUANTITY />
          <UNIT />
          <VALUE />
        </COMMODITY>
        """

        commodity_id = int_or_none(get_xml_val(xml, "./COMMODITY_ID"))
        commodity_desc = get_xml_val(xml, "./COMMODITY_DESC")
        quantity = decimal_or_none(get_xml_val(xml, "./QUANTITY"))
        value = decimal_or_none(get_xml_val(xml, "./VALUE"))

        if None in (commodity_id, commodity_desc, quantity, value):
            return None

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "commodity_id": commodity_id,
                "goods_description": commodity_desc,
                "quantity_amount": quantity,
                "value": value,
            }
        )


class WoodContractParser(BaseXmlParser):
    MODEL = dm.WoodContractFile
    PARENT = dm.WoodQuotaApplication
    FIELD = "contract_files_xml"
    ROOT_NODE = "/CONTRACT_LIST/CONTRACT"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: "ET") -> dm.WoodContractFile | None:
        """Example XML structure

        <CONTRACT>
          <TARGET_ID />
          <CONTRACT_DATE />
          <CONTRACT_REFERENCE />
        </CONTRACT>
        """

        target_id = int_or_none(get_xml_val(xml, "./TARGET_ID[not(fox-error)]"))
        contract_date = date_or_none(get_xml_val(xml, "./CONTRACT_DATE[not(fox-error)]"))
        reference = get_xml_val(xml, "./CONTRACT_REFERENCE[not(fox-error)]")

        if None in (target_id, contract_date, reference):
            return None

        return cls.MODEL(
            **{
                "import_application_id": parent_pk,
                "target_id": target_id,
                "contract_date": contract_date,
                "reference": reference,
            }
        )


class OPTCommodity(BaseXmlParser):
    PARENT = dm.OutwardProcessingTradeApplication
    MODEL = dm.OPTCpCommodity
    ROOT_NODE = "/COMMODITY_LIST/COMMODITY"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        """Example XML structure

        <COMMODITY>
          <COMMODITY_ID />
        </COMMODITY>
        """

        commodity_id = int_or_none(get_xml_val(xml, "./COMMODITY_ID[not(fox-error)]"))

        if not commodity_id:
            return None

        return cls.MODEL(
            **{
                "outwardprocessingtradeapplication_id": parent_pk,
                "commodity_id": commodity_id,
            }
        )


class OPTCpCommodity(OPTCommodity):
    FIELD = "cp_commodities_xml"


class OPTTegCommodity(OPTCommodity):
    MODEL = dm.OPTTegCommodity
    FIELD = "teg_commodities_xml"


class ConstabularyEmailAttachments(BaseXmlParser):
    PARENT = dm.CaseEmail
    FIELD = "constabulary_attachments_xml"
    MODEL = dm.ConstabularyEmailAttachments
    ROOT_NODE = "/FIREARMS_CERTIFICATE_LIST/FIREARMS_CERTIFICATE"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        """Example XML structure

        <FIREARMS_CERTIFICATE_LIST>
          <FIREARMS_CERTIFICATE>
            <TARGET_ID />
            <CERTIFICATE_REF />
            <CERTIFICATE_TYPE />
            <CONSTABULARY />
            <EXPIRY_DATE />
            <SELECT_FLAG />
            <IS_IMPORTER_DOCUMENT />
          </FIREARMS_CERTIFICATE>
        </FIREARMS_CERTIFICATE_LIST>
        """

        if get_xml_val(xml, "./SELECT_FLAG") != "true":
            return None

        target_id = int_or_none(get_xml_val(xml, "./TARGET_ID"))

        if not target_id:
            return None

        return cls.MODEL(
            **{
                "caseemail_id": parent_pk,
                "file_target_id": target_id,
            }
        )
