from django.db import models

from web.domains.commodity.models import Commodity
from web.domains.file.models import File

from ..models import ImportApplication


class SanctionsAndAdhocApplication(ImportApplication):
    PROCESS_TYPE = "SanctionsAndAdhocApplication"

    exporter_name = models.CharField(max_length=4096, blank=True, null=True)
    exporter_address = models.CharField(max_length=4096, blank=True, null=True)
    supporting_documents = models.ManyToManyField(File)


class SanctionsAndAdhocApplicationGoods(models.Model):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    commodity_code = models.ForeignKey(Commodity, on_delete=models.PROTECT)
    goods_description = models.CharField(max_length=4096)
    quantity_amount = models.DecimalField(max_digits=9, decimal_places=2)
    value = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return (
            f"{self.import_application} - "
            f"{self.commodity_code} - "
            f"{self.quantity_amount} - "
            f"{self.value}"
        )
