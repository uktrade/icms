from itertools import chain
from typing import Literal, Union, final

from django.db import models
from django.db.models import QuerySet
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
from web.types import TypedTextChoices

ReportFirearms = list[
    Union[
        "SILSupplementaryReportFirearmSection1",
        "SILSupplementaryReportFirearmSection2",
        "SILSupplementaryReportFirearmSection5",
        "SILSupplementaryReportFirearmSection582Obsolete",  # /PS-IGNORE
        "SILSupplementaryReportFirearmSection582Other",  # /PS-IGNORE
    ]
]

SectionCertificates = Union[
    QuerySet["SILGoodsSection1"],
    QuerySet["SILGoodsSection2"],
    QuerySet["SILGoodsSection5"],
    QuerySet["SILGoodsSection582Obsolete"],  # /PS-IGNORE
    QuerySet["SILGoodsSection582Other"],  # /PS-IGNORE
]


class SILUserSection5(File):
    """User uploaded section 5 documents."""


@final
class SILApplication(ImportApplication):
    """Firearms Specific Import Licence Application."""

    PROCESS_TYPE = ProcessTypes.FA_SIL
    IS_FINAL = True

    # Select one or more sections related to the firearms licence
    section1 = models.BooleanField(verbose_name="Section 1", default=False)
    section2 = models.BooleanField(verbose_name="Section 2", default=False)
    section5 = models.BooleanField(verbose_name="Section 5", default=False)
    section58_obsolete = models.BooleanField(
        verbose_name="Section 58(2) - Obsolete Calibre", default=False
    )
    section58_other = models.BooleanField(verbose_name="Section 58(2) - Other", default=False)

    # Section for old legacy applications from v1 - Never populated in V2
    # Earlier records didn't record the section the goods apply for.
    section_legacy = models.BooleanField("Unknown Section", default=False)

    other_description = models.CharField(
        max_length=4000,
        null=True,
        blank=True,
        verbose_name="Other Section Description",
        help_text="Please explain why you are making this request under this 'Other' section.",
    )

    # Question related to the firearms
    military_police = models.BooleanField(
        null=True, verbose_name="Are any of your items for the military or police?"
    )
    eu_single_market = models.BooleanField(
        null=True,
        verbose_name="Were any of your items in the EU Single Market before 14 September 2018?",
    )
    manufactured = models.BooleanField(
        null=True, verbose_name="Were any of your items manufactured before 1 September 1939?"
    )

    # Goods
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

    # Details of who bought from
    know_bought_from = models.BooleanField(
        null=True, verbose_name="Do you know who you plan to buy/obtain these items from?"
    )

    # misc
    additional_comments = models.CharField(max_length=4000, blank=True, null=True)

    # section 5
    user_section5 = models.ManyToManyField("web.SILUserSection5", related_name="sil_application")
    verified_section5 = models.ManyToManyField("web.Section5Authority", related_name="+")

    # certificates
    user_imported_certificates = models.ManyToManyField(
        "UserImportCertificate", related_name="sil_application"
    )
    verified_certificates = models.ManyToManyField(
        "FirearmsAuthority", related_name="sil_application"
    )


class SILGoodsSection1(models.Model):
    import_application = models.ForeignKey(
        "web.SILApplication", on_delete=models.PROTECT, related_name="goods_section1"
    )
    is_active = models.BooleanField(default=True)

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured before 1900?", null=True
    )

    description = models.CharField(
        max_length=4096,
        help_text=(
            "You no longer need to type the part of the Firearms Act that applies to the"
            " item listed in this box. You must select it from the 'Licence for' section."
        ),
    )

    quantity = models.PositiveBigIntegerField(help_text="Enter a whole number")


class SILGoodsSection2(models.Model):
    import_application = models.ForeignKey(
        "web.SILApplication", on_delete=models.PROTECT, related_name="goods_section2"
    )
    is_active = models.BooleanField(default=True)

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured before 1900?", null=True
    )

    description = models.CharField(
        max_length=4096,
        help_text=(
            "You no longer need to type the part of the Firearms Act that applies to the"
            " item listed in this box. You must select it from the 'Licence for' section."
        ),
    )

    quantity = models.PositiveBigIntegerField(help_text="Enter a whole number")


class SILGoodsSection5(models.Model):
    import_application = models.ForeignKey(
        "web.SILApplication", on_delete=models.PROTECT, related_name="goods_section5"
    )
    is_active = models.BooleanField(default=True)

    subsection = models.CharField(max_length=300, verbose_name="Section 5 subsection")

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured before 1900?", null=True
    )

    description = models.CharField(
        max_length=4096,
        help_text=(
            "You no longer need to type the part of the Firearms Act that applies to the"
            " item listed in this box. You must select it from the 'Licence for' section."
        ),
    )

    quantity = models.PositiveBigIntegerField(
        blank=True, null=True, help_text="Enter a whole number"
    )
    unlimited_quantity = models.BooleanField(verbose_name="Unlimited Quantity", default=False)


class SILGoodsSection582Obsolete(models.Model):  # /PS-IGNORE
    import_application = models.ForeignKey(
        "web.SILApplication", on_delete=models.PROTECT, related_name="goods_section582_obsoletes"
    )
    is_active = models.BooleanField(default=True)

    curiosity_ornament = models.BooleanField(
        verbose_name="Do you intend to possess the firearm as a 'curiosity or ornament'?", null=True
    )
    acknowledgement = models.BooleanField(
        verbose_name="Do you acknowledge the above statement?", default=False
    )

    centrefire = models.BooleanField(
        verbose_name="Is this a breech-loading centrefire firearm?", null=True
    )

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured after 1899 and before 1939?", null=True
    )

    original_chambering = models.BooleanField(
        verbose_name="Does the firearm retain its original chambering?", null=True
    )

    obsolete_calibre = models.CharField(max_length=200, verbose_name="Obsolete Calibre")

    description = models.CharField(
        max_length=4096,
        help_text=(
            "You no longer need to type the part of the Firearms Act that applies to the"
            " item listed in this box. You must select it from the 'Licence for' section."
        ),
    )

    quantity = models.PositiveBigIntegerField(help_text="Enter a whole number")


class SILGoodsSection582Other(models.Model):  # /PS-IGNORE
    class IgnitionDetail(TypedTextChoices):
        PIN_FIRE = ("Pin-fire", "Pin-fire")
        NEEDDLE_FIRE = ("Needle-fire", "Needle-fire")
        LIP_FIRE = ("Lip-fire", "Lip-fire")
        CUP_PRIMED = ("Cup primed", "Cup primed")
        TEAT_FIRE = ("Teat-fire", "Teat-fire")
        BASE_FIRE = ("Base-fire", "Base-fire")
        OTHER = ("Other", "Other")

    import_application = models.ForeignKey(
        "web.SILApplication", on_delete=models.PROTECT, related_name="goods_section582_others"
    )
    is_active = models.BooleanField(default=True)

    curiosity_ornament = models.BooleanField(
        verbose_name="Do you intend to possess the firearm as a 'curiosity or ornament'?", null=True
    )
    acknowledgement = models.BooleanField(
        verbose_name="Do you acknowledge the above statement?",
        default=False,
    )

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured after 1899 and before 1939?", null=True
    )

    muzzle_loading = models.BooleanField(verbose_name="Is the firearm muzzle-loading?", null=True)

    rimfire = models.BooleanField(
        verbose_name="Is the firearm breech-loading capable of discharging a rimfire cartridge other than .22 inch, .23 inch, 6mm or 9mm?",
        null=True,
    )
    rimfire_details = models.CharField(
        max_length=50, verbose_name="If Yes, please specify", blank=True
    )

    ignition = models.BooleanField(
        verbose_name="Is the firearm breech-loading using an ignition system other than rimfire or centrefire?",
        null=True,
    )
    ignition_details = models.CharField(
        choices=IgnitionDetail.choices,
        max_length=12,
        verbose_name="If Yes, please specify ignition system",
        blank=True,
    )
    ignition_other = models.CharField(
        max_length=20, verbose_name="If Other, please specify", blank=True
    )

    chamber = models.BooleanField(
        verbose_name="Is the firearm a shotgun, punt gun or rifle chambered for one of the following cartridges (expressed in imperial measurements)?",
        null=True,
        help_text=(
            "32 bore, 24 bore, 14 bore, 10 bore (2 5/8 and 2 7/8 inch only), 8 bore, 4 bore,"
            " 3 bore, 2 bore, 1 1/8 bore, 1 1/2 bore, 1 1/4 bore"
        ),
    )

    bore = models.BooleanField(
        verbose_name="Is the firearm a shotgun, punt gun or rifle with a bore greater than 10?",
        null=True,
    )
    bore_details = models.CharField(
        max_length=50,
        verbose_name="If Yes, please specify",
        blank=True,
    )

    description = models.CharField(
        max_length=4096,
        help_text=(
            "You no longer need to type the part of the Firearms Act that applies to the"
            " item listed in this box. You must select it from the 'Licence for' section."
        ),
    )

    quantity = models.PositiveBigIntegerField(help_text="Enter a whole number")


class SILLegacyGoods(models.Model):
    """Model to hold historic SIL goods where we can't determine the section they apply to"""

    import_application = models.ForeignKey(
        "web.SILApplication", on_delete=models.PROTECT, related_name="goods_legacy"
    )
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=4096)
    quantity = models.PositiveBigIntegerField(null=True, help_text="Enter a whole number")
    unlimited_quantity = models.BooleanField(verbose_name="Unlimited Quantity", default=False)
    obsolete_calibre = models.CharField(max_length=200, verbose_name="Obsolete Calibre", null=True)


class SILChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        "web.SILApplication", on_delete=models.PROTECT, related_name="checklist"
    )

    authority_required = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess required?",
    )

    authority_received = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess received?",
    )

    authority_cover_items_listed = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess covers items listed?",
    )

    quantities_within_authority_restrictions = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Quantities listed within authority to possess restrictions?",
    )

    authority_police = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to possess checked with police?",
    )


class SILSupplementaryInfo(SupplementaryInfoBase):
    import_application = models.OneToOneField(
        "web.SILApplication", on_delete=models.CASCADE, related_name="supplementary_info"
    )


class SILSupplementaryReport(SupplementaryReportBase):
    supplementary_info = models.ForeignKey(
        "web.SILSupplementaryInfo", related_name="reports", on_delete=models.CASCADE
    )

    def goods_sections(self) -> list[str]:
        return [
            "section1",
            "section2",
            "section5",
            "section582-obsolete",
            "section582-other",
            "section_legacy",
        ]

    def get_section_certificates(self, section_type: str) -> SectionCertificates:
        section_mapping = {
            "section1": "goods_section1",
            "section2": "goods_section2",
            "section5": "goods_section5",
            "section582-obsolete": "goods_section582_obsoletes",
            "section582-other": "goods_section582_others",
            "section_legacy": "goods_legacy",
        }

        app = self.supplementary_info.import_application

        try:
            app_section = section_mapping[section_type]
        except KeyError:
            raise NotImplementedError(f"section_type is not supported: {section_type}")

        return getattr(app, app_section).filter(is_active=True)

    def get_report_firearms(
        self, is_manual: bool = False, is_upload: bool = False, is_no_firearm: bool = False
    ) -> ReportFirearms:
        """Method to filter all report firearms on a firearm report.

        :param is_manual: Firearm information which was manually entered
        :param is_upload: Firearm information which was uploaded as a document
        :param is_no_firearm: No information included for firearm
        """

        return list(
            chain(
                self.section1_firearms.filter(
                    is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
                ),
                self.section2_firearms.filter(
                    is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
                ),
                self.section5_firearms.filter(
                    is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
                ),
                self.section582_obsolete_firearms.filter(
                    is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
                ),
                self.section582_other_firearms.filter(
                    is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
                ),
                self.section_legacy_firearms.filter(
                    is_manual=is_manual, is_upload=is_upload, is_no_firearm=is_no_firearm
                ),
            )
        )

    def get_add_firearm_url(
        self, section_type: str, section_pk: int, url_type: Literal["manual", "no-firearm"]
    ) -> str:
        if url_type not in ["manual", "no-firearm"]:
            raise NotImplementedError(f"Invalid url type {url_type}")

        return reverse(
            f"import:fa-sil:report-firearm-{url_type}-add",
            kwargs={
                "application_pk": self.supplementary_info.import_application.pk,
                "sil_section_type": section_type,
                "report_pk": self.pk,
                "section_pk": section_pk,
            },
        )


class SILSupplementaryReportFirearmBase(SupplementaryReportFirearmBase):
    class Meta:
        abstract = True

    def get_description(self) -> str:
        return self.goods_certificate.description

    def get_manual_url(self, url_type: Literal["edit", "delete"], section_type: str) -> str:
        return reverse(
            f"import:fa-sil:report-firearm-manual-{url_type}",
            kwargs={
                "application_pk": self.report.supplementary_info.import_application.pk,
                "sil_section_type": section_type,
                "report_pk": self.report.pk,
                "section_pk": self.goods_certificate.pk,
                "report_firearm_pk": self.pk,
            },
        )


# TODO ICMSLST-1883:  SILSupplementaryReport firearms need to be able to handle documents
#  Added to the models as part of ICMSLST-1756. Need to add to the frontend also


class SILSupplementaryReportFirearmSection1(SILSupplementaryReportFirearmBase):
    report = models.ForeignKey(
        "web.SILSupplementaryReport", related_name="section1_firearms", on_delete=models.CASCADE
    )
    goods_certificate = models.ForeignKey(
        "web.SILGoodsSection1",
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )


class SILSupplementaryReportFirearmSection2(SILSupplementaryReportFirearmBase):
    report = models.ForeignKey(
        "web.SILSupplementaryReport", related_name="section2_firearms", on_delete=models.CASCADE
    )
    goods_certificate = models.ForeignKey(
        "web.SILGoodsSection2",
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )


class SILSupplementaryReportFirearmSection5(SILSupplementaryReportFirearmBase):
    report = models.ForeignKey(
        "web.SILSupplementaryReport", related_name="section5_firearms", on_delete=models.CASCADE
    )
    goods_certificate = models.ForeignKey(
        "web.SILGoodsSection5",
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )


class SILSupplementaryReportFirearmSection582Obsolete(  # /PS-IGNORE
    SILSupplementaryReportFirearmBase
):
    report = models.ForeignKey(
        "web.SILSupplementaryReport",
        related_name="section582_obsolete_firearms",
        on_delete=models.CASCADE,
    )
    goods_certificate = models.ForeignKey(
        "web.SILGoodsSection582Obsolete",  # /PS-IGNORE
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )


class SILSupplementaryReportFirearmSection582Other(SILSupplementaryReportFirearmBase):  # /PS-IGNORE
    report = models.ForeignKey(
        "web.SILSupplementaryReport",
        related_name="section582_other_firearms",
        on_delete=models.CASCADE,
    )
    goods_certificate = models.ForeignKey(
        "web.SILGoodsSection582Other",  # /PS-IGNORE
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )


class SILSupplementaryReportFirearmSectionLegacy(SILSupplementaryReportFirearmBase):
    report = models.ForeignKey(
        "web.SILSupplementaryReport",
        related_name="section_legacy_firearms",
        on_delete=models.CASCADE,
    )
    goods_certificate = models.ForeignKey(
        "web.SILLegacyGoods",
        related_name="supplementary_report_firearms",
        on_delete=models.CASCADE,
    )
    document = models.OneToOneField(
        "web.File", related_name="+", null=True, on_delete=models.SET_NULL
    )
