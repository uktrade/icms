from django.db import models

from web.domains.case._import.models import ChecklistBase
from web.domains.file.models import File
from web.domains.section5.models import Section5Authority
from web.models.shared import FirearmCommodity, YesNoNAChoices

from ..models import ImportApplication, ImportApplicationType


class SILUserSection5(File):
    """User uploaded section 5 documents."""


class SILApplication(ImportApplication):
    """Firearms Specific Import Licence Application."""

    PROCESS_TYPE = ImportApplicationType.ProcessTypes.FA_SIL

    # Select one or more sections related to the firearms licence
    section1 = models.BooleanField(verbose_name="Section 1", default=False)
    section2 = models.BooleanField(verbose_name="Section 2", default=False)
    section5 = models.BooleanField(verbose_name="Section 5", default=False)
    section58_obsolete = models.BooleanField(
        verbose_name="Section 58(2) - Obsolete Calibre", default=False
    )
    section58_other = models.BooleanField(verbose_name="Section 58(2) - Other", default=False)
    other_description = models.CharField(
        max_length=4000,
        null=True,
        blank=True,
        verbose_name="Other Section Description",
        help_text=(
            "If you have selected Other in Firearms Act Sections. Please explain why you are making"
            " this request under this 'Other' section."
        ),
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

    # Details of who bought from
    know_bought_from = models.BooleanField(null=True)

    # misc
    additional_comments = models.CharField(max_length=4000, blank=True, null=True)

    # section 5
    user_section5 = models.ManyToManyField(SILUserSection5, related_name="sil_application")
    verified_section5 = models.ManyToManyField(Section5Authority, related_name="+")

    # certificates
    user_imported_certificates = models.ManyToManyField(
        "UserImportCertificate", related_name="sil_application"
    )
    verified_certificates = models.ManyToManyField(
        "FirearmsAuthority", related_name="sil_application"
    )


class SILGoodsSection1(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section1"
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

    quantity = models.PositiveIntegerField(help_text="Enter a whole number")


class SILGoodsSection2(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section2"
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

    quantity = models.PositiveIntegerField(help_text="Enter a whole number")


class SILGoodsSection5(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section5"
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

    quantity = models.PositiveIntegerField(blank=True, null=True, help_text="Enter a whole number")
    unlimited_quantity = models.BooleanField(verbose_name="Unlimited Quantity", default=False)


class SILGoodsSection582Obsolete(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_obsoletes"
    )
    is_active = models.BooleanField(default=True)

    curiosity_ornament = models.BooleanField(
        verbose_name="Do you intend to possess the firearm as a 'curiosity or ornament'?", null=True
    )
    acknowledgment = models.BooleanField(
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

    obsolete_calibre = models.CharField(max_length=50, verbose_name="Obsolete Calibre")

    description = models.CharField(
        max_length=4096,
        help_text=(
            "You no longer need to type the part of the Firearms Act that applies to the"
            " item listed in this box. You must select it from the 'Licence for' section."
        ),
    )

    quantity = models.PositiveIntegerField(help_text="Enter a whole number")


class SILGoodsSection582Other(models.Model):
    class IgnitionDetail(models.TextChoices):
        PIN_FIRE = ("Pin-fire", "Pin-fire")
        NEEDDLE_FIRE = ("Needle-fire", "Needle-fire")
        LIP_FIRE = ("Lip-fire", "Lip-fire")
        CUP_PRIMED = ("Cup primed", "Cup primed")
        TEAT_FIRE = ("Teat-fire", "Teat-fire")
        BASE_FIRE = ("Base-fire", "Base-fire")
        OTHER = ("Other", "Other")

    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_others"
    )
    is_active = models.BooleanField(default=True)

    curiosity_ornament = models.BooleanField(
        verbose_name="Do you intend to possess the firearm as a 'curiosity or ornament'?", null=True
    )
    acknowledgment = models.BooleanField(
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

    quantity = models.PositiveIntegerField(help_text="Enter a whole number")


class SILChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        SILApplication, on_delete=models.PROTECT, related_name="checklist"
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
