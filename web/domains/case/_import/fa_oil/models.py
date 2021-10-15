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
from web.models import UserImportCertificate
from web.models.shared import FirearmCommodity, YesNoNAChoices

if TYPE_CHECKING:
    from django.db.models import QuerySet


@final
class OpenIndividualLicenceApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.FA_OIL
    IS_FINAL = True

    section1 = models.BooleanField(verbose_name="Section 1", default=True)
    section2 = models.BooleanField(verbose_name="Section 2", default=True)

    know_bought_from = models.BooleanField(null=True)

    user_imported_certificates = models.ManyToManyField(
        UserImportCertificate, related_name="oil_application"
    )
    verified_certificates = models.ManyToManyField(
        "FirearmsAuthority", related_name="oil_application"
    )

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

    @staticmethod
    def goods_description() -> str:
        return (
            "Firearms, component parts thereof, or ammunition of any applicable "
            "commodity code, other than those falling under Section 5 of the "
            "Firearms Act 1968 as amended."
        )


class ChecklistFirearmsOILApplication(ChecklistBase):
    import_application = models.OneToOneField(
        OpenIndividualLicenceApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    authority_required = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess required?",
    )
    authority_received = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess received?",
    )
    authority_police = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess checked with police?",
    )


class OILSupplementaryInfo(SupplementaryInfoBase):
    import_application = models.OneToOneField(
        OpenIndividualLicenceApplication,
        on_delete=models.CASCADE,
        related_name="supplementary_info",
    )


class OILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        OILSupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )

    def get_goods_certificates(self) -> list[str]:
        return [OpenIndividualLicenceApplication.goods_description()]

    def get_report_firearms(
        self, is_manual: bool = False, is_upload: bool = False, is_no_firearm: bool = False
    ) -> "QuerySet[OILSupplementaryReportFirearm]":
        """Method to filter all report firearms on a firearm report.

        :param is_manual: Firearm information which was manually entered
        :param is_upload: Firearm information which was uploaded as a document
        :param is_no_firearm: No information included for firearm
        """

        return self.firearms.filter(
            is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
        )

    def get_add_firearm_url(self, url_type: Literal["manual", "upload", "no-firearm"]) -> str:
        if url_type not in ["manual", "upload", "no-firearm"]:
            raise NotImplementedError(f"Invalid url type {url_type}")

        return reverse(
            f"import:fa-oil:report-firearm-{url_type}-add",
            kwargs={
                "application_pk": self.supplementary_info.import_application.pk,
                "report_pk": self.pk,
            },
        )


class OILSupplementaryReportFirearm(SupplementaryReportFirearmBase):
    report = models.ForeignKey(
        OILSupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )

    document = models.OneToOneField(File, related_name="+", null=True, on_delete=models.SET_NULL)

    def get_description(self) -> str:
        return OpenIndividualLicenceApplication.goods_description()

    def get_manual_url(self, url_type: Literal["edit", "delete"]) -> str:
        return reverse(
            f"import:fa-oil:report-firearm-manual-{url_type}",
            kwargs={
                "application_pk": self.report.supplementary_info.import_application.pk,
                "report_pk": self.report.pk,
                "report_firearm_pk": self.pk,
            },
        )

    def get_view_upload_url(self) -> str:
        return reverse(
            "import:fa-oil:report-firearm-upload-view",
            kwargs={
                "application_pk": self.report.supplementary_info.import_application.pk,
                "report_pk": self.report.pk,
                "report_firearm_pk": self.pk,
            },
        )
