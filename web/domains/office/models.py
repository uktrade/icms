from django.db import models


class Office(models.Model):
    """Office for importer/exporters"""

    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    EMPTY = "EMPTY"
    ENTRY_TYPES = ((MANUAL, "Manual"), (SEARCH, "Search"), (EMPTY, "Empty"))

    is_active = models.BooleanField(blank=False, null=False, default=True)

    # These max_length values match the lengths that we can send CHIEF.
    address_1 = models.CharField(max_length=35, verbose_name="Address line 1")
    address_2 = models.CharField(
        max_length=35, null=True, blank=True, verbose_name="Address line 2"
    )
    address_3 = models.CharField(
        max_length=35, null=True, blank=True, verbose_name="Address line 3"
    )
    address_4 = models.CharField(
        max_length=35, null=True, blank=True, verbose_name="Address line 4"
    )
    address_5 = models.CharField(
        max_length=35, null=True, blank=True, verbose_name="Address line 5"
    )
    postcode = models.CharField(max_length=8)

    eori_number = models.CharField(max_length=20, blank=True, null=True)
    address_entry_type = models.CharField(max_length=10, blank=False, null=False, default=EMPTY)

    def get_status(self):
        return "Current" if self.is_active else "Archived"

    def __str__(self):
        return f"{self.address}\n{self.postcode}"

    @property
    def address(self) -> str:
        """The old db column "address" was used in several places.

        Maintain existing behaviour using an address property.
        """

        fields = [self.address_1, self.address_2, self.address_3, self.address_4, self.address_5]
        return "\n".join(f for f in fields if f)
