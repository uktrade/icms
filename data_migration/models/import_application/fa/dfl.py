from typing import Any, Generator, Tuple

from django.db import models
from django.db.models import OuterRef, Q, Subquery
from lxml import etree

from data_migration.models.base import MigrationBase
from data_migration.models.file import File, FileTarget
from data_migration.models.import_application.import_application import (
    ChecklistBase,
    ImportApplication,
)
from data_migration.models.reference.country import Country
from data_migration.models.reference.fa import Constabulary
from data_migration.utils.format import get_xml_val, int_or_none

from .base import (
    FirearmBase,
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)


class DFLApplication(FirearmBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", unique=True
    )
    deactivated_firearm = models.BooleanField(default=True)
    proof_checked = models.BooleanField(default=False)
    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT, null=True)
    fa_goods_certs_xml = models.TextField(null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "DFLSupplementaryInfo"]


class DFLGoodsCertificate(MigrationBase):
    target = models.ForeignKey(FileTarget, related_name="+", on_delete=models.PROTECT)
    dfl_application = models.ForeignKey(
        DFLApplication,
        on_delete=models.PROTECT,
        related_name="+",
    )
    goods_description = models.CharField(max_length=4096, null=True)
    deactivated_certificate_reference = models.CharField(max_length=50, null=True)
    legacy_id = models.IntegerField(null=True)

    issuing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
    )

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values() + ["file_ptr_id"]
        sub_query = File.objects.filter(target_id=OuterRef("target_id"))

        # Exclude unsubmitted applications where reference, constabulary or expiry_date are null
        exclude_query = Q(dfl_application__imad__submit_datetime__isnull=True) & Q(
            Q(goods_description__isnull=True)
            | Q(deactivated_certificate_reference__isnull=True)
            | Q(issuing_country__isnull=True)
        )

        return (
            cls.objects.select_related("target")
            .prefetch_related("target__files")
            .annotate(
                file_ptr_id=Subquery(sub_query.values("pk")[:1]),
            )
            .exclude(file_ptr_id__isnull=True)
            .exclude(exclude_query)
            .values(*values)
            .iterator()
        )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        # This is a M2M field in V2
        data.pop("dfl_application_id")

        # Remove id and set file_ptr_id because V2 inherits from File model
        data.pop("id")
        return data

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": data["id"],
            "dflgoodscertificate_id": data["file_ptr_id"],
            "dflapplication_id": data["dfl_application_id"],
        }

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["legacy_id", "target_id"]

    @classmethod
    def parse_xml(cls, batch: list[Tuple[int, str]]) -> list[models.Model]:
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

        model_list = []
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

                # Add the legacy ordinal to the object so it can be referenced later
                # The supplementary reports will use the same ordinal to link to the correct goods
                obj.legacy_ordinal = i
                model_list.append(obj)
        return model_list

    @classmethod
    def parse_xml_fields(cls, parent_pk: int, xml: etree.ElementTree) -> "DFLGoodsCertificate":
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

        return cls(
            **{
                "dfl_application_id": parent_pk,
                "target_id": int_or_none(target_id),
                "deactivated_certificate_reference": reference,
                "goods_description": description,
                "issuing_country_id": int_or_none(issuing_country),
            }
        )


class DFLChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", related_name="+"
    )
    deactivation_certificate_attached = models.CharField(max_length=3, null=True)
    deactivation_certificate_issued = models.CharField(max_length=3, null=True)


class DFLSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.CASCADE,
        related_name="+",
        to_field="imad_id",
    )


class DFLSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        DFLSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class DFLSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        DFLSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )

    goods_certificate_legacy_id = models.IntegerField()
    document = models.OneToOneField(File, related_name="+", null=True, on_delete=models.SET_NULL)

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values() + ["goods_certificate_id"]
        sub_query = DFLGoodsCertificate.objects.filter(
            legacy_id=OuterRef("goods_certificate_legacy_id"),
            dfl_application_id=OuterRef("report__supplementary_info__imad__id"),
        )

        return (
            cls.objects.select_related("report__supplementary_info__imad")
            .annotate(
                goods_certificate_id=Subquery(sub_query.values("target__files__pk")[:1]),
            )
            .exclude(goods_certificate_id__isnull=True)
            .values(*values)
            .iterator()
        )
