from django.db import models

from ..models import ImportApplication


class SILApplication(ImportApplication):
    """Firearms Specific Import Licence Application."""

    PROCESS_TYPE = "SILApplication"

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


class SILGoodsSection1(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section1"
    )

    manufacture = models.BooleanField(verbose_name="Was the firearm manufactured before 1900?")

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


class SILGoodsSection2(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section2"
    )

    manufacture = models.BooleanField(verbose_name="Was the firearm manufactured before 1900?")

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


class SILGoodsSection5(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section5"
    )

    subsection = models.CharField(max_length=200, verbose_name="Section 5 subsection")

    manufacture = models.BooleanField(verbose_name="Was the firearm manufactured before 1900?")

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()
    unlimited_quantity = models.BooleanField(verbose_name="Unlimited Quantity", null=True)


class SILGoodsSection582Obsolete(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_obsoletes"
    )

    curiosity_ornament = models.BooleanField(
        verbose_name="Do you intend to possess the firearm as a 'curiosity or ornament'?"
    )
    acknowledgment = models.BooleanField(verbose_name="Do you acknowledge the above statement?")

    centrefire = models.BooleanField(verbose_name="Is this a breech-loading centrefire firearm?")

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured after 1899 and before 1939?"
    )

    original_chambering = models.BooleanField(
        verbose_name="Does the firearm retain its original chambering?"
    )

    obsolete_calibre = models.CharField(max_length=50, verbose_name="Obsolete Calibre")

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()


class SILGoodsSection582Other(models.Model):
    import_application = models.ForeignKey(
        SILApplication, on_delete=models.PROTECT, related_name="goods_section582_others"
    )

    curiosity_ornament = models.BooleanField(
        verbose_name="Do you intend to possess the firearm as a 'curiosity or ornament'?"
    )
    acknowledgment = models.BooleanField(verbose_name="Do you acknowledge the above statement?")

    manufacture = models.BooleanField(
        verbose_name="Was the firearm manufactured after 1899 and before 1939?"
    )

    muzzle_loading = models.BooleanField(verbose_name="Is the firearm muzzle-loading?")

    rimfire = models.BooleanField(
        verbose_name="Is the firearm breech-loading capable of discharging a rimfire cartridge other than .22 inch, .23 inch, 6mm or 9mm?"
    )
    rimfire_details = models.CharField(max_length=50, verbose_name="If Yes, please specify")

    ignition = models.BooleanField(
        verbose_name="Is the firearm breech-loading using an ignition system other than rimfire or centrefire?"
    )
    ignition_details = models.BooleanField(verbose_name="If Yes, please specify ignition system")

    chamber = models.BooleanField(
        verbose_name="Is the firearm a shotgun, punt gun or rifle chambered for one of the following cartridges (expressed in imperial measurements)?"
    )

    bore = models.BooleanField(
        verbose_name="Is the firearm a shotgun, punt gun or rifle with a bore greater than 10?"
    )
    bore_details = models.CharField(
        max_length=50,
        verbose_name="Is the firearm a shotgun, punt gun or rifle with a bore greater than 10?",
    )

    description = models.CharField(max_length=4096)

    quantity = models.IntegerField()
