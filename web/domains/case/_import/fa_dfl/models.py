from typing import TYPE_CHECKING, Literal, final

from django.db import models
from django.urls import reverse

from web.domains.case._import.fa.models import (
    SupplementaryInfoBase,
    SupplementaryReportBase,
    SupplementaryReportFirearmBase,
)
from web.domains.case._import.models import ChecklistBase, ImportApplication
from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import FirearmCommodity, YesNoNAChoices

if TYPE_CHECKING:
    from django.db.models import QuerySet


class DFLGoodsCertificate(File):
    """Deactivated Firearms Licence Goods certificate"""

    goods_description = models.CharField(max_length=4096, verbose_name="Goods Description")

    # Field for case officer to override the description that appears on the licence
    goods_description_override = models.CharField(
        max_length=4096, verbose_name="Goods Description", null=True
    )

    deactivated_certificate_reference = models.CharField(
        max_length=50, verbose_name="Deactivated Certificate Reference"
    )

    issuing_country = models.ForeignKey(
        "web.Country",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Issuing Country",
        blank=False,
        null=False,
        limit_choices_to={"is_active": True},
    )

    def __str__(self):
        dcf = self.deactivated_certificate_reference
        return f"DFLGoodsCertificate(id={self.pk}, deactivated_certificate_reference={dcf!r})"


@final
class DFLApplication(ImportApplication):
    """Firearms & Ammunition Deactivated Firearms Licence application"""

    PROCESS_TYPE = ProcessTypes.FA_DFL
    IS_FINAL = True

    deactivated_firearm = models.BooleanField(verbose_name="Deactivated Firearm", default=True)
    proof_checked = models.BooleanField(verbose_name="Proof Checked", default=False)

    # Goods section fields
    commodity_code = models.CharField(
        max_length=13,
        null=True,
        default=FirearmCommodity.EX_CHAPTER_93,
        choices=FirearmCommodity.choices,
        verbose_name="Commodity Code",
        help_text=(
            "You must pick the commodity code group that applies to the items that you wish to"
            ' import. Please note that "ex Chapter 97" is only relevant to collectors pieces and'
            " items over 100 years old. Please contact HMRC classification advisory service,"
            " 01702 366077, if you are unsure of the correct code."
        ),
    )

    constabulary = models.ForeignKey("web.Constabulary", on_delete=models.PROTECT, null=True)
    goods_certificates = models.ManyToManyField(
        "web.DFLGoodsCertificate", related_name="dfl_application"
    )

    know_bought_from = models.BooleanField(
        null=True, verbose_name="Do you know who you plan to buy/obtain these items from?"
    )

    def __str__(self):
        return f"DFLApplication(id={self.pk}, status={self.status!r}, is_active={self.is_active})"


class DFLChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        "web.DFLApplication", on_delete=models.PROTECT, related_name="checklist"
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


class DFLSupplementaryInfo(SupplementaryInfoBase):
    import_application = models.OneToOneField(
        "web.DFLApplication", on_delete=models.CASCADE, related_name="supplementary_info"
    )


class DFLSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        "web.DFLSupplementaryInfo", related_name="reports", on_delete=models.CASCADE
    )

    def get_goods_certificates(self) -> "QuerySet[DFLGoodsCertificate]":
        return self.supplementary_info.import_application.goods_certificates.filter(is_active=True)

    def get_report_firearms(
        self, is_manual: bool = False, is_upload: bool = False, is_no_firearm: bool = False
    ) -> "QuerySet[DFLSupplementaryReportFirearm]":
        """Method to filter all report firearms on a firearm report.

        :param is_manual: Firearm information which was manually entered
        :param is_upload: Firearm information which was uploaded as a document
        :param is_no_firearm: No information included for firearm
        """

        return self.firearms.filter(
            is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
        )

    def get_add_firearm_url(
        self, goods_pk: int, url_type: Literal["manual", "upload", "no-firearm"]
    ) -> str:
        if url_type not in ["manual", "upload", "no-firearm"]:
            raise NotImplementedError(f"Invalid url type {url_type}")

        return reverse(
            f"import:fa-dfl:report-firearm-{url_type}-add",
            kwargs={
                "application_pk": self.supplementary_info.import_application.pk,
                "goods_pk": goods_pk,
                "report_pk": self.pk,
            },
        )


class DFLSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        "web.DFLSupplementaryReport", related_name="firearms", on_delete=models.CASCADE
    )

    goods_certificate = models.ForeignKey(
        "web.DFLGoodsCertificate",
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )

    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )

    def get_description(self) -> str:
        return self.goods_certificate.goods_description

    def get_manual_url(self, url_type: Literal["edit", "delete"]) -> str:
        return reverse(
            f"import:fa-dfl:report-firearm-manual-{url_type}",
            kwargs={
                "application_pk": self.report.supplementary_info.import_application.pk,
                "report_pk": self.report.pk,
                "report_firearm_pk": self.pk,
            },
        )

    def get_view_upload_url(self) -> str:
        return reverse(
            "import:fa-dfl:report-firearm-upload-view",
            kwargs={
                "application_pk": self.report.supplementary_info.import_application.pk,
                "report_pk": self.report.pk,
                "report_firearm_pk": self.pk,
            },
        )
