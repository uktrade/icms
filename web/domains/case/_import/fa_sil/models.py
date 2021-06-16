from django.db import models

from web.domains.case._import.models import ChecklistBase
from web.domains.file.models import File
from web.domains.section5.models import Section5Authority
from web.models.shared import YesNoNAChoices

from ..models import ImportApplication, ImportApplicationType


class SILUserSection5(File):
    """User uploaded section 5 documents."""


class SILApplication(ImportApplication):
    """Firearms Specific Import Licence Application."""

    PROCESS_TYPE = ImportApplicationType.ProcessTypes.FA_SIL

    # Select one or more sections related to the firearms licence
    section1 = models.BooleanField(null=True)
    section2 = models.BooleanField(null=True)
    section5 = models.BooleanField(null=True)
    section58_obsolete = models.BooleanField(null=True)
    section58_other = models.BooleanField(null=True)
    other_description = models.CharField(max_length=4000, null=True, blank=True)

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
    commodity_code = models.CharField(max_length=40, blank=False, null=True)

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

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


class SILGoodsSection2(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section2"
    )
    is_active = models.BooleanField(default=True)

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured before 1900?", null=True
    )

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


class SILGoodsSection5(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section5"
    )
    is_active = models.BooleanField(default=True)

    subsection = models.CharField(max_length=300, verbose_name="Section 5 subsection")

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured before 1900?", null=True
    )

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField(blank=True, null=True)
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

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


class SILGoodsSection582Other(models.Model):
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
        max_length=10, verbose_name="If Yes, please specify ignition system", blank=True
    )
    ignition_other = models.CharField(
        max_length=20, verbose_name="If Other, please specify", blank=True
    )

    chamber = models.BooleanField(
        verbose_name="Is the firearm a shotgun, punt gun or rifle chambered for one of the following cartridges (expressed in imperial measurements)?",
        null=True,
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

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


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
