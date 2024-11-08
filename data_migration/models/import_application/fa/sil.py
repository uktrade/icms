from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import File
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


class SILApplicationFirearmAuthority(MigrationBase):
    silapplication = models.ForeignKey(SILApplication, on_delete=models.CASCADE)
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)


class SILApplicationSection5Authority(MigrationBase):
    silapplication = models.ForeignKey(SILApplication, on_delete=models.CASCADE)
    section5authority = models.ForeignKey(Section5Authority, on_delete=models.CASCADE)


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
    description_original = models.CharField(max_length=4096, null=True)
    quantity_original = models.PositiveBigIntegerField(null=True)
    description = models.CharField(max_length=4096, null=True)
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
    legacy_ordinal = models.PositiveIntegerField()


class SILGoodsSection2(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section2"
    )
    is_active = models.BooleanField(default=True)
    manufacture = models.BooleanField(null=True)
    description_original = models.CharField(max_length=4096, null=True)
    quantity_original = models.PositiveBigIntegerField(null=True)
    description = models.CharField(max_length=4096, null=True)
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
    description_original = models.CharField(max_length=4096, null=True)
    quantity_original = models.PositiveBigIntegerField(null=True)
    description = models.CharField(max_length=4096, null=True)
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
    obsolete_calibre_legacy = models.ForeignKey(
        ObsoleteCalibre, on_delete=models.PROTECT, to_field="legacy_id"
    )
    description_original = models.CharField(max_length=4096, null=True)
    quantity_original = models.PositiveBigIntegerField(null=True)
    description = models.CharField(max_length=4096, null=True)
    quantity = models.PositiveBigIntegerField(null=True)
    legacy_ordinal = models.PositiveIntegerField()


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
    description_original = models.CharField(max_length=4096, null=True)
    quantity_original = models.PositiveBigIntegerField(null=True)
    description = models.CharField(max_length=4096, null=True)
    quantity = models.PositiveBigIntegerField(null=True)
    legacy_ordinal = models.PositiveIntegerField()


class SILLegacyGoods(MigrationBase):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_legacy"
    )
    is_active = models.BooleanField(default=True)
    description_original = models.CharField(max_length=4096, null=True)
    quantity_original = models.PositiveBigIntegerField(null=True)
    description = models.CharField(max_length=4096, null=True)
    quantity = models.PositiveBigIntegerField(null=True)
    unlimited_quantity = models.BooleanField(default=False)
    obsolete_calibre_legacy = models.ForeignKey(
        ObsoleteCalibre, on_delete=models.SET_NULL, to_field="legacy_id", null=True
    )
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

    GOODS_MODEL: type[models.Model] | None = None


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
