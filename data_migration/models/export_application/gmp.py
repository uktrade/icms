from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber

from data_migration.models.base import MigrationBase
from data_migration.models.file import File, FileFolder

from .export import ExportApplication, ExportBase


class CertificateOfGoodManufacturingPracticeApplication(ExportBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    file_folder = models.OneToOneField(FileFolder, on_delete=models.CASCADE, related_name="gmp")
    is_responsible_person = models.CharField(max_length=3, null=True)
    responsible_person_name = models.CharField(max_length=200, null=True)
    responsible_person_address_entry_type = models.CharField(max_length=10, default="MANUAL")
    responsible_person_postcode = models.CharField(max_length=30, null=True)
    responsible_person_address = models.CharField(max_length=4000, null=True)
    responsible_person_country = models.CharField(max_length=3, null=True)
    is_manufacturer = models.CharField(max_length=3, null=True)
    manufacturer_name = models.CharField(max_length=200, null=True)
    manufacturer_address_entry_type = models.CharField(max_length=10, default="MANUAL")
    manufacturer_postcode = models.CharField(max_length=30, null=True)
    manufacturer_address = models.CharField(max_length=4000, null=True)
    manufacturer_country = models.CharField(max_length=3, null=True)
    gmp_certificate_issued = models.CharField(max_length=10, null=True)
    auditor_accredited = models.CharField(max_length=3, null=True)
    auditor_certified = models.CharField(max_length=3, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        cert = data["gmp_certificate_issued"]
        cert_map = {"ISO22716": "ISO_22716", "BRCGS": "BRC_GSOCP"}

        if cert in cert_map:
            data["gmp_certificate_issued"] = cert_map[cert]

        return data

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return super().models_to_populate() + ["GMPBrand"]


class GMPFile(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        # V2 file types have an underscore after 3rd charatcer
        file_type = data.pop("file_type")

        if file_type == "BRCGS":
            data["file_type"] = "BRC_GSOCP"
        else:
            data["file_type"] = file_type[:3] + "_" + file_type[3:]

        return data

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            File.objects.select_related("target__folder__gmp_id")
            .filter(
                target__folder__folder_type="GMP_SUPPORTING_DOCUMENTS",
                target__folder__gmp__isnull=False,
            )
            .values(file_type=F("target__target_type"), file_ptr_id=F("id"))
            .iterator(chunk_size=2000)
        )

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            File.objects.select_related("target__folder__gmp_id")
            .filter(
                target__folder__folder_type="GMP_SUPPORTING_DOCUMENTS",
                target__folder__gmp__isnull=False,
            )
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                gmpfile_id=F("pk"),
                certificateofgoodmanufacturingpracticeapplication_id=F("target__folder__gmp__pk"),
            )
            .iterator(chunk_size=2000)
        )


class GMPBrand(MigrationBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    brand_name = models.CharField(max_length=100, null=True)

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            cls.objects.filter(brand_name__isnull=False)
            .values("id", "brand_name", application_id=F("cad__id"))
            .iterator(chunk_size=2000)
        )
