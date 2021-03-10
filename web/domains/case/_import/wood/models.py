from django.db import models

from ..models import ImportApplication


class WoodQuotaApplication(ImportApplication):
    PROCESS_TYPE = "WoodQuotaApplication"

    shipping_year = models.IntegerField(blank=False, null=True)

    # exporter
    exporter_name = models.CharField(max_length=100, blank=False, null=True)
    exporter_address = models.CharField(max_length=4000, blank=False, null=True)
    exporter_vat_nr = models.CharField(max_length=100, blank=False, null=True)

    #  goods
    commodity_code = models.CharField(max_length=40, blank=False, null=True)
    goods_description = models.CharField(max_length=100, blank=False, null=True)
    goods_qty = models.DecimalField(blank=False, null=True, max_digits=9, decimal_places=2)
    goods_unit = models.CharField(max_length=40, blank=False, null=True)

    # TODO: add the fields for the rest of the data:
    #  ICMSLST-557: certificates/documents
    #  ICMSLST-558: supporting documents
