from collections import defaultdict
from typing import TYPE_CHECKING, Any, Generator, Optional

from lxml import etree

from data_migration import models as dm
from data_migration.utils.format import (
    date_or_none,
    get_xml_val,
    int_or_none,
    str_to_bool,
    str_to_yes_no,
    xml_str_or_none,
)

from .base import BaseXmlParser, BatchT, ModelListT

if TYPE_CHECKING:
    from django.db.models import Model

FA_TYPE_CODES = {
    "DEACTIVATED": "deactivated",
    "RFD": "registered",
    # "SHOTGUN": "shotgun", TODO ICMSLST-1519 correct the key to match V1
    # "FA": "firearms",  TODO ICMSLST-1519 correct the key to match V1
}


class ImportContactParser(BaseXmlParser):
    MODEL = dm.ImportContact
    PARENT = [dm.SILApplication, dm.OpenIndividualLicenceApplication, dm.DFLApplication]
    FIELD = "bought_from_details_xml"
    ROOT_NODE = "/SELLER_HOLDER_LIST/SELLER_HOLDER"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> dm.ImportContact:
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

        legacy_id = get_xml_val(xml, "./SELLER_HOLDER_ID/text()")
        entity = get_xml_val(xml, "./PERSON_DETAILS/PERSON_TYPE/text()")
        entity = entity.lower().strip("_person")
        if entity == "legal":
            first_name = get_xml_val(xml, "./PERSON_DETAILS/LEGAL_PERSON_NAME/text()")
        else:
            first_name = get_xml_val(xml, "./PERSON_DETAILS/FIRST_NAME/text()")
        last_name = get_xml_val(xml, "./PERSON_DETAILS/SURNAME/text()")
        registration_number = get_xml_val(xml, "./PERSON_DETAILS/REGISTRATION_NUMBER/text()")
        street = get_xml_val(xml, "./ADDRESS/STREET_AND_NUMBER/text()")
        city = get_xml_val(xml, "./ADDRESS/TOWN_CITY/text()")
        postcode = get_xml_val(xml, "./ADDRESS/POSTCODE/text()")
        region = get_xml_val(xml, "./ADDRESS/REGION/text()")
        dealer = get_xml_val(xml, "./IS_DEALER_FLAG/text()")
        country_id = get_xml_val(xml, "./ADDRESS/COUNTRY/text()")

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
            }
        )


class UserImportCertificateParser(BaseXmlParser):
    MODEL = dm.UserImportCertificate
    PARENT = [dm.SILApplication, dm.OpenIndividualLicenceApplication]
    FIELD = "fa_certs_xml"
    ROOT_NODE = "/FIREARMS_CERTIFICATE_LIST/FIREARMS_CERTIFICATE"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.UserImportCertificate]:
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
        target_id = get_xml_val(xml, "./TARGET_ID/text()")
        certificate_type = get_xml_val(xml, "./CERTIFICATE_TYPE/text()")

        if not target_id or not certificate_type:
            # There needs to be an file and certificate_type associated with the data
            return None

        reference = get_xml_val(xml, "./CERTIFICATE_REF/text()")
        constabulary_id = get_xml_val(xml, "./CONSTABULARY/text()")
        date_issued = get_xml_val(xml, "./DATE_ISSUED/text()")
        expiry_date = get_xml_val(xml, "./EXPIRY_DATE/text()")

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
                section = get_xml_val(xml, "./SECTION/text()")

                if not section:
                    continue

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
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
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

        section = get_xml_val(xml, "./SECTION/text()")
        return getattr(cls, f"parse_{section.lower()}")(parent_pk, xml)

    @classmethod
    def parse_sec_base(cls, parent_pk, xml) -> dict[str, Any]:
        description = get_xml_val(xml, "./COMMODITY_DESC/text()")
        manufacture = get_xml_val(xml, "./MANUFACTURED_BEFORE_1900/text()")
        quantity = get_xml_val(xml, "./QUANTITY/text()")

        return {
            "import_application_id": parent_pk,
            "description": description,
            "manufacture": str_to_bool(manufacture),
            "quantity": int_or_none(quantity),
        }

    @classmethod
    def parse_sec1(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        return dm.SILGoodsSection1(**cls.parse_sec_base(parent_pk, xml))

    @classmethod
    def parse_sec2(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        return dm.SILGoodsSection2(**cls.parse_sec_base(parent_pk, xml))

    @classmethod
    def parse_sec5(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)

        subsection = get_xml_val(xml, "./SECTION_5_CLAUSE/text()")
        unlimited_quantity = get_xml_val(xml, "./QUANTITY_UNLIMITED_FLAG/text()")

        return dm.SILGoodsSection5(
            **data
            | {
                "subsection": subsection,
                "unlimited_quantity": bool(str_to_bool(unlimited_quantity)),
            }
        )

    @classmethod
    def parse_obsolete_calibre(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)

        acknowledgement = get_xml_val(xml, "./CURIOSITY_STATEMENT_AGREED/text()")
        centrefire = get_xml_val(xml, "./BREECH_LOADING_CENTREFIRE/text()")
        curiosity_ornament = get_xml_val(xml, "./CURIOSITY_OR_ORNAMENT/text()")
        manufacture = get_xml_val(xml, "./MANUFACTURED_AFTER_1899_BEFORE_1939/text()")
        obsolete_calibre = get_xml_val(xml, "./OBSOLETE_CALIBRE/OC_ID/text()")
        original_chambering = get_xml_val(xml, "./ORIGINAL_CHAMBERING/text()")

        return dm.SILGoodsSection582Obsolete(  # /PS-IGNORE
            **data
            | {
                "acknowledgement": str_to_bool(acknowledgement),
                "centrefire": str_to_bool(centrefire),
                "curiosity_ornament": str_to_bool(curiosity_ornament),
                "manufacture": str_to_bool(manufacture),
                "obsolete_calibre_id": int_or_none(obsolete_calibre),
                "original_chambering": str_to_bool(original_chambering),
            }
        )

    @classmethod
    def parse_other(cls, parent_pk: int, xml: etree.ElementTree) -> Optional["Model"]:
        data = cls.parse_sec_base(parent_pk, xml)

        acknowledgement = get_xml_val(xml, "./CURIOSITY_STATEMENT_AGREED/text()")
        bore = get_xml_val(xml, "./SHOTGUN_PUNTGUN_RIFLE_OVER_10_BORE/text()")
        bore_details = get_xml_val(xml, "./SHOTGUN_PUNTGUN_RIFLE_OVER_10_BORE_SPECIFIED/text()")
        chamber = get_xml_val(xml, "./SHOTGUN_PUNTGUN_RIFLE_LISTED_CARTRIDGES/text()")
        curiosity_ornament = get_xml_val(xml, "./CURIOSITY_OR_ORNAMENT/text()")
        ignition = get_xml_val(xml, "./OTHER_IGNITION_SYSTEM/text()")
        ignition_details = get_xml_val(xml, "./OTHER_IGNITION_SYSTEM_SPECIFIED/text()")
        ignition_other = get_xml_val(xml, "./OTHER_IGNITION_SYSTEM_SPECIFIED_OTHER/text()")
        manufacture = get_xml_val(xml, "./MANUFACTURED_AFTER_1899_BEFORE_1939/text()")
        muzzle_loading = get_xml_val(xml, "./MUZZLE_LOADING/text()")
        rimfire = get_xml_val(xml, "./OTHER_BREECH_RIMFIRE_CARTRIDGE/text()")
        rimfire_details = get_xml_val(xml, "./OTHER_BREECH_RIMFIRE_CARTRIDGE_SPECIFIED/text()")

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


class SupplementaryReportParser(BaseXmlParser):
    FIELD = "supplementary_report_xml"
    ROOT_NODE = "/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> dm.SupplementaryReportBase:
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

        transport = get_xml_val(xml, ".//MODE_OF_TRANSPORT[not(fox-error)]/text()")
        date_received = get_xml_val(xml, ".//RECEIVED_DATE[not(fox-error)]/text()")
        report_firearms_xml = get_xml_val(xml, ".//GOODS_LINE_LIST")
        bought_from_legacy_id = get_xml_val(xml, ".//REPORT_SELLER_HOLDER[not(fox-error)]/text()")

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
          </GOODS_LINE>
        </GOODS_LINE_LIST>
        """

        if not cls.MODEL:
            raise NotImplementedError("MODEL must be defined on the class")

        model_list: ModelListT = defaultdict(list)
        for parent_pk, xml in batch:
            xml_tree = etree.fromstring(xml)
            goods_xml_list = xml_tree.xpath(cls.ROOT_NODE)
            for ordinal, goods_xml in enumerate(goods_xml_list, start=1):
                reporting_mode = get_xml_val(goods_xml, "./FA_REPORTING_MODE/text()")

                if reporting_mode == "MANUAL":
                    report_firearm_xml_list = goods_xml.xpath(".//FIREARMS_DETAILS")
                    for report_firearm_xml in report_firearm_xml_list:
                        obj = cls.parse_manual_xml(parent_pk, report_firearm_xml)
                        obj.goods_certificate_legacy_id = ordinal
                        model_list[obj._meta.model].append(obj)

                elif reporting_mode == "UPLOAD":
                    model_list[cls.MODEL].append(
                        cls.MODEL(
                            report_id=parent_pk, is_upload=True, goods_certificate_legacy_id=ordinal
                        )
                    )
                    # TODO ICMSLST-1496: Report firearms need to connect to documents
                    # report_firearm_xml_list = goods_xml.xpath("/FIREARMS_DETAILS_LIST")

                else:
                    # TODO ICMSLST-1496: Check no firearms reported
                    model_list[cls.MODEL].append(
                        cls.MODEL(
                            report_id=parent_pk,
                            is_no_firearm=True,
                            goods_certificate_legacy_id=ordinal,
                        )
                    )

        return model_list

    @classmethod
    def parse_manual_xml(cls, parent_pk: int, xml: etree.ElementTree) -> "Model":
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

        serial_number = get_xml_val(xml, "./SERIAL_NUMBER/text()")
        calibre = get_xml_val(xml, "./CALIBRE/text()")
        model = get_xml_val(xml, "./MAKE_MODEL/text()")
        proofing = get_xml_val(xml, "./PROOFING/text()")

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
    }

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
            .iterator()
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
          </GOODS_LINE>
        </GOODS_LINE_LIST>
        """

        model_list: ModelListT = defaultdict(list)

        for parent_pk, xml, section, ordinal in batch:
            xml_tree = etree.fromstring(xml)
            goods_index = ordinal - 1
            goods_xml_list = xml_tree.xpath(cls.ROOT_NODE)
            goods_xml = goods_xml_list[goods_index]
            reporting_mode = get_xml_val(goods_xml, "./FA_REPORTING_MODE/text()")

            model = cls.SECTION_MODEL[section]

            if reporting_mode == "MANUAL":
                report_firearm_xml_list = goods_xml.xpath(".//FIREARMS_DETAILS")
                for report_firearm_xml in report_firearm_xml_list:
                    obj = cls.parse_manual_xml(parent_pk, model, report_firearm_xml)
                    obj.goods_certificate_legacy_id = ordinal
                    model_list[model].append(obj)

            elif reporting_mode == "UPLOAD":
                model_list[model].append(
                    model(report_id=parent_pk, is_upload=True, goods_certificate_legacy_id=ordinal)
                )
                # TODO ICMSLST-1496: Report firearms need to connect to documents
                # report_firearm_xml_list = goods_xml.xpath("/FIREARMS_DETAILS_LIST")

            else:
                # TODO ICMSLST-1496: Check no firearms reported
                model_list[model].append(
                    model(
                        report_id=parent_pk,
                        is_no_firearm=True,
                        goods_certificate_legacy_id=ordinal,
                    )
                )

        return model_list

    @classmethod
    def parse_manual_xml(
        cls, parent_pk: int, goods_model: "Model", xml: etree.ElementTree
    ) -> "Model":
        """Exmaple XML structure

        <FIREARMS_DETAILS>
          <SERIAL_NUMBER />
          <CALIBRE />
          <MAKE_MODEL />
          <PROOFING />
        </FIREARMS_DETAILS>
        """

        serial_number = get_xml_val(xml, "./SERIAL_NUMBER/text()")
        calibre = get_xml_val(xml, "./CALIBRE/text()")
        model = get_xml_val(xml, "./MAKE_MODEL/text()")
        proofing = get_xml_val(xml, "./PROOFING/text()")

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
            xml_zip = zip(cert_list, commodity_list)
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
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> dm.DFLGoodsCertificate:
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

        target_id = get_xml_val(xml, "./FIREARMS_CERTIFICATE/TARGET_ID/text()")
        reference = get_xml_val(xml, "./FIREARMS_CERTIFICATE/CERTIFICATE_REF/text()")
        issuing_country = get_xml_val(xml, "./FIREARMS_CERTIFICATE/ISSUING_COUNTRY/text()")
        description = get_xml_val(xml, "./COMMODITY/COMMODITY_DESC/text()")

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
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.OILApplicationFirearmAuthority]:
        """Example XML structure

        <AUTHORITY>
          <IA_ID />
          <SELECTED />
        </AUTHORITY>
        """

        ia_id = int_or_none(get_xml_val(xml, "./IA_ID/text()"))
        selected = str_to_bool(get_xml_val(xml, "./SELECTED/text()"))

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
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.SILApplicationFirearmAuthority]:
        """Example XML structure

        <AUTHORITY>
          <IA_ID />
          <SELECTED />
        </AUTHORITY>
        """

        ia_id = int_or_none(get_xml_val(xml, "./IA_ID/text()"))
        selected = str_to_bool(get_xml_val(xml, "./SELECTED/text()"))

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
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.SILApplicationFirearmAuthority]:
        """Example XML structure

        <AUTHORITY>
          <IA_ID />
          <SELECTED />
        </AUTHORITY>
        """

        ia_id = int_or_none(get_xml_val(xml, "./IA_ID/text()"))
        selected = str_to_bool(get_xml_val(xml, "./SELECTED/text()"))

        if not selected or not ia_id:
            return None

        return cls.MODEL(**{"silapplication_id": parent_pk, "section5authority_id": ia_id})


class ClauseQuantityParser(BaseXmlParser):
    MODEL = dm.ClauseQuantity
    PARENT = dm.Section5Authority
    FIELD = "clause_quantity_xml"
    ROOT_NODE = "/GOODS_CATEGORY_LIST/GOODS_CATEGORY"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.ClauseQuantity]:
        """Example XML structure

        <GOODS_CATEGORY>
          <CATEGORY_ID />
          <QUANTITY_WRAPPER>
            <QUANTITY />
            <UNLIMITED_QUANTITY />
          </QUANTITY_WRAPPER>
        </GOODS_CATEGORY>
        """

        clause_id = int_or_none(get_xml_val(xml, "./CATEGORY_ID/text()"))
        quantity = int_or_none(get_xml_val(xml, "./QUANTITY_WRAPPER/QUANTITY/text()"))
        infinity = str_to_bool(get_xml_val(xml, "./QUANTITY_WRAPPER/UNLIMITED_QUANTITY/text()"))

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
    PARENT = dm.Section5Authority
    FIELD = "act_quantity_xml"
    ROOT_NODE = "/GOODS_CATEGORY_LIST/GOODS_CATEGORY"

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> Optional[dm.ActQuantity]:
        """Example XML structure

        <GOODS_CATEGORY>
          <CATEGORY_ID />
          <QUANTITY_WRAPPER>
            <QUANTITY />
            <UNLIMITED_QUANTITY />
          </QUANTITY_WRAPPER>
        </GOODS_CATEGORY>
        """

        act_id = int_or_none(get_xml_val(xml, "./CATEGORY_ID/text()"))
        quantity = int_or_none(get_xml_val(xml, "./QUANTITY_WRAPPER/QUANTITY/text()"))
        infinity = str_to_bool(get_xml_val(xml, "./QUANTITY_WRAPPER/UNLIMITED_QUANTITY/text()"))

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


class FirearmsAuthorityFileParser(BaseXmlParser):
    MODEL = dm.FirearmsAuthorityFile
    PARENT = dm.FirearmsAuthority
    FIELD = "file_target_xml"
    ROOT_NODE = "/FF_TARGET_LIST/FF_TARGET"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.FirearmsAuthorityFile]:
        """Example XML structure

        <FF_TARGET>
          <FFT_ID />
          <VERSION />
        </FF_TARGET>
        """

        target_id = int_or_none(get_xml_val(xml, "./FFT_ID"))

        if not target_id:
            return None

        return cls.MODEL(**{"firearmsauthority_id": parent_pk, "filetarget_id": target_id})


class Section5AuthorityFileParser(BaseXmlParser):
    MODEL = dm.Section5AuthorityFile
    PARENT = dm.Section5Authority
    FIELD = "file_target_xml"
    ROOT_NODE = "/FF_TARGET_LIST/FF_TARGET"

    @classmethod
    def parse_xml_fields(
        cls, parent_pk: int, xml: etree.ElementTree
    ) -> Optional[dm.Section5AuthorityFile]:
        """Example XML structure

        <FF_TARGET>
          <FFT_ID />
          <VERSION />
        </FF_TARGET>
        """

        target_id = int_or_none(get_xml_val(xml, "./FFT_ID"))

        if not target_id:
            return None

        return cls.MODEL(**{"section5authority_id": parent_pk, "filetarget_id": target_id})
