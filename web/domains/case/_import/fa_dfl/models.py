from django.db import models

from web.domains.case._import.models import ChecklistBase, ImportApplication
from web.domains.constabulary.models import Constabulary
from web.domains.country.models import Country
from web.domains.file.models import File


class DFLGoodsCertificate(File):
    """Deactivated Firearms Licence Goods certificate"""

    goods_description = models.CharField(max_length=4096, verbose_name="Goods Description")

    deactivated_certificate_reference = models.CharField(
        max_length=50, verbose_name="Deactivated Certificate Reference"
    )

    issuing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Issuing Country",
        blank=False,
        null=False,
    )

    def __str__(self):
        dcf = self.deactivated_certificate_reference
        return f"DFLGoodsCertificate(id={self.pk}, deactivated_certificate_reference={dcf!r})"


class DFLApplication(ImportApplication):
    """Firearms & Ammunition Deactivated Firearms Licence application"""

    class CommodityCodes(models.TextChoices):
        EX_CHAPTER_93 = ("ex Chapter 93", "ex Chapter 93")
        EX_CHAPTER_97 = ("ex Chapter 97", "ex Chapter 97")

    PROCESS_TYPE = "DFLApplication"

    deactivated_firearm = models.BooleanField(verbose_name="Deactivated Firearm", default=True)
    proof_checked = models.BooleanField(verbose_name="Proof Checked", default=False)

    # Goods section fields
    commodity_code = models.CharField(
        max_length=40,
        blank=False,
        null=True,
        choices=CommodityCodes.choices,
        verbose_name="Commodity Code",
    )
    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT, null=True)
    goods_certificates = models.ManyToManyField(DFLGoodsCertificate, related_name="+")

    know_bought_from = models.BooleanField(
        blank=False,
        null=True,
        verbose_name="Do you know who you plan to buy/obtain these items from?",
    )

    def __str__(self):
        return f"DFLApplication(id={self.pk}, status={self.status!r}, is_active={self.is_active})"


class DFLChecklist(ChecklistBase):
    import_application = models.ForeignKey(
        DFLApplication, on_delete=models.PROTECT, related_name="checklists"
    )

    deactivation_certificate_attached = models.CharField(
        max_length=3,
        choices=ChecklistBase.Response.choices,
        null=True,
        verbose_name="Deactivation certificate attached?",
    )

    deactivation_certificate_issued = models.CharField(
        max_length=3,
        choices=ChecklistBase.Response.choices,
        null=True,
        verbose_name="Deactivation certificate issued by competent authority?",
    )
