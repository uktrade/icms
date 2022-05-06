from typing import Any, Generator, Optional, Type

from django.db import models
from django.db.models import OuterRef, Subquery

from data_migration.models.base import MigrationBase
from data_migration.models.reference import ObsoleteCalibre

from ..import_application import ImportApplication
from .base import (
    FirearmBase,
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)


class SILApplication(FirearmBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.PROTECT,
        to_field="imad_id",
        unique=True,
        related_name="sil",
    )
    section1 = models.BooleanField(default=False)
    section2 = models.BooleanField(default=False)
    section5 = models.BooleanField(default=False)
    section58_obsolete = models.BooleanField(default=False)
    section58_other = models.BooleanField(default=False)
    other_description = models.CharField(max_length=4000, null=True)
    military_police = models.BooleanField(null=True)
    eu_single_market = models.BooleanField(null=True)
    manufactured = models.BooleanField(null=True)
    additional_comments = models.CharField(max_length=4000, null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "SILSupplementaryInfo"]


# TODO ICMSLST-1548: SILUserSection5 M2M
# TODO ICMSLST-1548: Section5Authority M2M
# TODO ICMSLST-1548: FirearmAuthorityM2M


class SILSection(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section"
    )
    legacy_ordinal = models.IntegerField()
    section = models.CharField(max_length=20)


class SILGoodsSection1(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section1"
    )
    is_active = models.BooleanField(default=True)
    manufacture = models.BooleanField(null=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField()
    legacy_ordinal = models.PositiveIntegerField()

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["legacy_ordinal"]


class SILGoodsSection2(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section2"
    )
    is_active = models.BooleanField(default=True)
    manufacture = models.BooleanField(null=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField()
    legacy_ordinal = models.PositiveIntegerField()


class SILGoodsSection5(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section5"
    )
    is_active = models.BooleanField(default=True)
    subsection = models.CharField(max_length=300)
    manufacture = models.BooleanField(null=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
    legacy_ordinal = models.PositiveIntegerField()


class SILGoodsSection582Obsolete(MigrationBase):  # /PS-IGNORE
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_obsoletes"
    )
    is_active = models.BooleanField(default=True)
    curiosity_ornament = models.BooleanField(null=True)
    acknowledgement = models.BooleanField(default=False)
    centrefire = models.BooleanField(null=True)
    manufacture = models.BooleanField(null=True)
    original_chambering = models.BooleanField(null=True)
    obsolete_calibre = models.ForeignKey(
        ObsoleteCalibre, on_delete=models.PROTECT, to_field="legacy_id"
    )
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField()
    legacy_ordinal = models.PositiveIntegerField()

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["obsolete_calibre"] = data.pop("obsolete_calibre_name")
        return data

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["obsolete_calibre_id"]

    @classmethod
    def get_includes(cls) -> list[str]:
        return super().get_includes() + ["obsolete_calibre__name"]


class SILGoodsSection582Other(MigrationBase):  # /PS-IGNORE
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_others"
    )
    is_active = models.BooleanField(default=True)
    curiosity_ornament = models.BooleanField(null=True)
    acknowledgement = models.BooleanField(default=False)
    manufacture = models.BooleanField(null=True)
    muzzle_loading = models.BooleanField(null=True)
    rimfire = models.BooleanField(null=True)
    rimfire_details = models.CharField(max_length=50, default="")
    ignition = models.BooleanField(null=True)
    ignition_details = models.CharField(max_length=12, default="")
    ignition_other = models.CharField(max_length=20, default="")
    chamber = models.BooleanField(null=True)
    bore = models.BooleanField(null=True)
    bore_details = models.CharField(max_length=50, default="")
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField()
    legacy_ordinal = models.PositiveIntegerField()


class SILSupplementaryInfo(SupplementaryInfoBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.CASCADE,
        related_name="supplementary_info",
        to_field="imad_id",
    )


class SILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        SILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )


class SILReportFirearmBase(SupplementaryReportFirearmBase):
    class Meta:
        abstract = True

    GOODS_MODEL: Optional[Type[models.Model]] = None

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        if not cls.GOODS_MODEL:
            raise NotImplementedError("GOODS_MODEL must be defined on the model")

        values = cls.get_values() + ["goods_certificate_id"]
        sub_query = cls.GOODS_MODEL.objects.filter(
            legacy_ordinal=OuterRef("goods_certificate_legacy_id"),
            import_application_id=OuterRef("report__supplementary_info__imad__id"),
        )

        return (
            cls.objects.select_related("report__supplementary_info__imad")
            .annotate(
                goods_certificate_id=Subquery(sub_query.values("pk")[:1]),
            )
            .exclude(goods_certificate_id__isnull=True)
            .values(*values)
            .iterator()
        )


class SILSupplementaryReportFirearmSection1(SILReportFirearmBase):
    GOODS_MODEL = SILGoodsSection1

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section1_firearms", on_delete=models.CASCADE
    )


class SILSupplementaryReportFirearmSection2(SILReportFirearmBase):
    GOODS_MODEL = SILGoodsSection2

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section2_firearms", on_delete=models.CASCADE
    )


class SILSupplementaryReportFirearmSection5(SILReportFirearmBase):
    GOODS_MODEL = SILGoodsSection5

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section5_firearms", on_delete=models.CASCADE
    )


class SILSupplementaryReportFirearmSection582Obsolete(SILReportFirearmBase):  # /PS-IGNORE
    GOODS_MODEL = SILGoodsSection582Obsolete  # /PS-IGNORE

    report = models.ForeignKey(
        SILSupplementaryReport,
        related_name="section582_obsolete_firearms",
        on_delete=models.CASCADE,
    )


class SILSupplementaryReportFirearmSection582Other(SILReportFirearmBase):  # /PS-IGNORE
    GOODS_MODEL = SILGoodsSection582Other  # /PS-IGNORE

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section582_other_firearms", on_delete=models.CASCADE
    )
