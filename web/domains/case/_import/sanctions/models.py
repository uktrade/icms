from django.db import models

from web.domains.commodity.models import Commodity
from web.domains.file.models import File

from ..models import ImportApplication, ImportApplicationType


class SanctionsAndAdhocApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.SANCTIONS

    exporter_name = models.CharField(max_length=4096, blank=True, null=True)
    exporter_address = models.CharField(max_length=4096, blank=True, null=True)
    supporting_documents = models.ManyToManyField(File)


class SanctionsAndAdhocApplicationGoods(models.Model):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Commodity Code",
        help_text=(
            "It is the responsibility of the applicant to ensure that the commodity code in"
            " this box is correct. If you are unsure of the correct commodity code,"
            " consult the HM Revenue and Customs Integrated Tariff Book, Volume 2,"
            " which is available from the Stationery Office. If you are still in doubt,"
            " contact the Classification Advisory Service on (01702) 366077."
        ),
    )

    goods_description = models.CharField(max_length=4096)
    quantity_amount = models.DecimalField(max_digits=9, decimal_places=2)
    value = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return (
            f"{self.import_application} - "
            f"{self.commodity} - "
            f"{self.quantity_amount} - "
            f"{self.value}"
        )
