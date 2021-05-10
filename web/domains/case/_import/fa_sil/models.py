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
