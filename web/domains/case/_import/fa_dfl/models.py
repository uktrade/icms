from typing import final

from django.db import models

from web.domains.case._import.fa.models import FirearmApplicationBase
from web.domains.case._import.models import ChecklistBase
from web.domains.constabulary.models import Constabulary
from web.domains.country.models import Country
from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import FirearmCommodity, YesNoNAChoices


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


@final
class DFLApplication(FirearmApplicationBase):
    """Firearms & Ammunition Deactivated Firearms Licence application"""

    PROCESS_TYPE = ProcessTypes.FA_DFL
    IS_FINAL = True

    deactivated_firearm = models.BooleanField(verbose_name="Deactivated Firearm", default=True)
    proof_checked = models.BooleanField(verbose_name="Proof Checked", default=False)

    # Goods section fields
    commodity_code = models.CharField(
        max_length=40,
        null=True,
        choices=FirearmCommodity.choices,
        verbose_name="Commodity Code",
        help_text=(
            "You must pick the commodity code group that applies to the items that you wish to"
            ' import. Please note that "ex Chapter 97" is only relevant to collectors pieces and'
            " items over 100 years old. Please contact HMRC classification advisory service,"
            " 01702 366077, if you are unsure of the correct code."
        ),
    )

    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT, null=True)
    goods_certificates = models.ManyToManyField(DFLGoodsCertificate, related_name="dfl_application")

    know_bought_from = models.BooleanField(
        blank=False,
        null=True,
        verbose_name="Do you know who you plan to buy/obtain these items from?",
    )

    def __str__(self):
        return f"DFLApplication(id={self.pk}, status={self.status!r}, is_active={self.is_active})"


class DFLChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        DFLApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    deactivation_certificate_attached = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Deactivation certificate attached?",
    )

    deactivation_certificate_issued = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Deactivation certificate issued by competent authority?",
    )
