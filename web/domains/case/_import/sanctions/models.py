from typing import final

from django.db import models

from web.domains.case._import.models import ImportApplication
from web.flow.models import ProcessTypes


@final
class SanctionsAndAdhocApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.SANCTIONS
    IS_FINAL = True

    exporter_name = models.CharField(max_length=4096, blank=True, null=True)
    exporter_address = models.CharField(max_length=4096, blank=True, null=True)
    supporting_documents = models.ManyToManyField("web.File")


class SanctionsAndAdhocApplicationGoods(models.Model):
    import_application = models.ForeignKey("web.ImportApplication", on_delete=models.CASCADE)
    commodity = models.ForeignKey(
        "web.Commodity",
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

    goods_description = models.CharField(max_length=4096, verbose_name="Goods Description")

    # CHIEF spec:
    # 9(n).9(m) decimal field with up to n digits before the decimal point and up to m digits after.
    # quantityIssued 9(11).9(3)
    quantity_amount = models.DecimalField(max_digits=14, decimal_places=3, verbose_name="Quantity")
    # value issued: 9(10).9(2)
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Value (GBP CIF)")

    def __str__(self):
        return (
            f"{self.import_application} - "
            f"{self.commodity} - "
            f"{self.quantity_amount} - "
            f"{self.value}"
        )
