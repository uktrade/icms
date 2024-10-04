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
    import_application = models.ForeignKey(
        "web.ImportApplication", on_delete=models.CASCADE, related_name="sanctions_goods"
    )
    commodity = models.ForeignKey(
        "web.Commodity",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Commodity Code",
    )

    goods_description = models.CharField(max_length=4096, verbose_name="Goods Description")
    # CHIEF spec:
    # 9(n).9(m) decimal field with up to n digits before the decimal point and up to m digits after.
    # quantityIssued 9(11).9(3)
    quantity_amount = models.DecimalField(max_digits=14, decimal_places=3, verbose_name="Quantity")
    # value issued: 9(10).9(2)
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Value (GBP CIF)",
        help_text=(
            "The value is the total value of all goods under the specified commodity code."
            " It is not the value of a single unit."
        ),
    )

    # Original values from applicant that cannot be overritten by case officer
    # TODO: ICMSLST-3017 Make fields not nullable when data migration is updated
    goods_description_original = models.CharField(max_length=4096, null=True)
    quantity_amount_original = models.DecimalField(max_digits=14, decimal_places=3, null=True)
    value_original = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    def __str__(self):
        return (
            f"{self.import_application} - "
            f"{self.commodity} - "
            f"{self.quantity_amount} - "
            f"{self.value}"
        )
