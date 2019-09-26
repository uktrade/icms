from django.db import models


class Office(models.Model):
    """Office for importer/exporters"""

    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    EMPTY = "EMPTY"
    ENTRY_TYPES = ((MANUAL, 'Manual'), (SEARCH, 'Search'), (EMPTY, 'Empty'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=4000, blank=False, null=True)
    eori_number = models.CharField(max_length=20, blank=True, null=True)
    address_entry_type = models.CharField(max_length=10,
                                          blank=False,
                                          null=False,
                                          default=EMPTY)
