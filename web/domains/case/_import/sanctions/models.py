from django.db import models

from web.domains.file.models import File

from ..models import ImportApplication, ImportApplicationType


class SanctionsAndAdhocApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.SANCTIONS

    exporter_name = models.CharField(max_length=4096, blank=True, null=True)
    exporter_address = models.CharField(max_length=4096, blank=True, null=True)
    supporting_documents = models.ManyToManyField(File)


class SanctionsAndAdhocApplicationGoods(models.Model):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    commodity_code = models.CharField(max_length=40, blank=False, null=True)
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
