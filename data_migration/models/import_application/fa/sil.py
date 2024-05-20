from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F, OuterRef, Subquery

from data_migration.models.base import MigrationBase
from data_migration.models.file import File, FileM2MBase
from data_migration.models.import_application import ChecklistBase, ImportApplication
from data_migration.models.reference import ObsoleteCalibre

from .authorities import FirearmsAuthority, Section5Authority, Section5Clause
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
    section5_authorities_xml = models.TextField(null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__, "SILSupplementaryInfo"]


class SILChecklist(ChecklistBase):
    imad = models.OneToOneField(
        ImportApplication,
        on_delete=models.PROTECT,
        to_field="imad_id",
        related_name="+",
    )
    authority_required = models.CharField(
        max_length=3,
        null=True,
    )
    authority_received = models.CharField(
        max_length=3,
        null=True,
    )
    authority_police = models.CharField(
        max_length=3,
        null=True,
    )
    auth_cover_items_listed = models.CharField(
        max_length=3,
        null=True,
    )
    within_auth_restrictions = models.CharField(
        max_length=3,
        null=True,
    )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["quantities_within_authority_restrictions"] = data.pop("within_auth_restrictions")
        data["authority_cover_items_listed"] = data.pop("auth_cover_items_listed")
        return data

    @classmethod
    def y_n_fields(cls) -> list[str]:
        return super().y_n_fields() + [
            "authority_required",
            "authority_received",
            "authority_police",
            "auth_cover_items_listed",
            "within_auth_restrictions",
        ]


class SILApplicationFirearmAuthority(MigrationBase):
    silapplication = models.ForeignKey(SILApplication, on_delete=models.CASCADE)
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)


class SILApplicationSection5Authority(MigrationBase):
    silapplication = models.ForeignKey(SILApplication, on_delete=models.CASCADE)
    section5authority = models.ForeignKey(Section5Authority, on_delete=models.CASCADE)


class SILUserSection5(FileM2MBase):
    TARGET_TYPE = "IMP_SECTION5_AUTHORITY"
    FILE_MODEL = "silusersection5"
    APP_MODEL = "silapplication"
    FILTER_APP_MODEL = False

    class Meta:
        abstract = True

    @classmethod
    def get_m2m_filter_kwargs(cls) -> dict[str, Any]:
        filter_kwargs = super().get_m2m_filter_kwargs()

        # Exclude docs that don't have an associated sil application
        filter_kwargs["target__folder__import_application__isnull"] = False

        return filter_kwargs

    @classmethod
    def get_source_data(cls) -> Generator:
        """The data for SILSection5User certificates are files with the the target_type of
        IMP_SECTION5_AUTHORITY and the folder_type of IMP_APP_DOCUMENTS.
        """
        filter_kwargs = cls.get_m2m_filter_kwargs()

        return (
            File.objects.filter(**filter_kwargs)
            .values(file_ptr_id=F("pk"))
            .iterator(chunk_size=2000)
        )


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
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
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
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
    legacy_ordinal = models.PositiveIntegerField()


class SILGoodsSection5(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section5"
    )
    is_active = models.BooleanField(default=True)
    section_5_code = models.ForeignKey(
        Section5Clause, on_delete=models.PROTECT, to_field="legacy_code"
    )
    manufacture = models.BooleanField(null=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
    legacy_ordinal = models.PositiveIntegerField()

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"section_5_clause_id": F("section_5_code__id")}

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["section_5_code_id"]


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
    obsolete_calibre_legacy = models.ForeignKey(
        ObsoleteCalibre, on_delete=models.PROTECT, to_field="legacy_id"
    )
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField()
    legacy_ordinal = models.PositiveIntegerField()

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["obsolete_calibre_legacy_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"obsolete_calibre": F("obsolete_calibre_legacy__name")}


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


class SILLegacyGoods(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_legacy"
    )
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
    obsolete_calibre_legacy = models.ForeignKey(
        ObsoleteCalibre, on_delete=models.SET_NULL, to_field="legacy_id", null=True
    )
    legacy_ordinal = models.PositiveIntegerField()

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["obsolete_calibre_legacy_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"obsolete_calibre": F("obsolete_calibre_legacy__name")}


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

    GOODS_MODEL: type[models.Model] | None = None

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
            .iterator(chunk_size=2000)
        )


class SILSupplementaryReportFirearmSection1(SILReportFirearmBase):
    GOODS_MODEL = SILGoodsSection1

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section1_firearms", on_delete=models.CASCADE
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")


class SILSupplementaryReportFirearmSection2(SILReportFirearmBase):
    GOODS_MODEL = SILGoodsSection2

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section2_firearms", on_delete=models.CASCADE
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")


class SILSupplementaryReportFirearmSection5(SILReportFirearmBase):
    GOODS_MODEL = SILGoodsSection5

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section5_firearms", on_delete=models.CASCADE
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")


class SILSupplementaryReportFirearmSection582Obsolete(SILReportFirearmBase):  # /PS-IGNORE
    GOODS_MODEL = SILGoodsSection582Obsolete  # /PS-IGNORE

    report = models.ForeignKey(
        SILSupplementaryReport,
        related_name="section582_obsolete_firearms",
        on_delete=models.CASCADE,
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")


class SILSupplementaryReportFirearmSection582Other(SILReportFirearmBase):  # /PS-IGNORE
    GOODS_MODEL = SILGoodsSection582Other  # /PS-IGNORE

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section582_other_firearms", on_delete=models.CASCADE
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")


class SILSupplementaryReportFirearmSectionLegacy(SILReportFirearmBase):
    GOODS_MODEL = SILLegacyGoods

    report = models.ForeignKey(
        SILSupplementaryReport, related_name="section_legacy_firearms", on_delete=models.CASCADE
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, to_field="sr_goods_file_id")
