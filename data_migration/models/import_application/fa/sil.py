from django.db import models

from data_migration.models.base import MigrationBase

from ..import_application import ImportApplication
from .base import FirearmBase, SupplementaryInfoBase, SupplementaryReportBase


class SILApplication(FirearmBase):
    imad = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, to_field="imad_id", unique=True
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
    acknowledgment = models.BooleanField(default=False)
    centrefire = models.BooleanField(null=True)
    manufacture = models.BooleanField(null=True)
    original_chambering = models.BooleanField(null=True)
    obsolete_calibre_id = models.IntegerField(null=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField()
    legacy_ordinal = models.PositiveIntegerField()


class SILGoodsSection582Other(MigrationBase):  # /PS-IGNORE
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_others"
    )
    is_active = models.BooleanField(default=True)
    curiosity_ornament = models.BooleanField(null=True)
    acknowledgment = models.BooleanField(default=False)
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
        related_name="+",
        to_field="imad_id",
    )


class SILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        SILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )
