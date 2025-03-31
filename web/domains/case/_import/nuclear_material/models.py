from typing import final

from django.db import models

from web.domains.case._import.models import ImportApplication
from web.flow.models import ProcessTypes
from web.types import TypedTextChoices


@final
class NuclearMaterialApplication(ImportApplication):
    class LicenceType(TypedTextChoices):
        SINGLE = ("S", "Single")
        OPEN = ("O", "Open")

    PROCESS_TYPE = ProcessTypes.NUCLEAR
    IS_FINAL = True

    nature_of_business = models.CharField(
        max_length=4096, default="", verbose_name="Nature of Business"
    )
    consignor_name = models.CharField(
        max_length=4096, default="", verbose_name="Consignor Company Name"
    )
    consignor_address = models.CharField(
        max_length=4096, default="", verbose_name="Consignor Company Address and Postcode"
    )

    end_user_name = models.CharField(
        max_length=4096, default="", verbose_name="End User Company Name"
    )
    end_user_address = models.CharField(
        max_length=4096, default="", verbose_name="End User Company Address and Postcode"
    )

    intended_use_of_shipment = models.TextField(
        default="", verbose_name="Intended end use of Shipment"
    )

    shipment_start_date = models.DateField(null=True)
    shipment_end_date = models.DateField(null=True)

    security_team_contact_information = models.TextField(
        default="", verbose_name="Contact Information for Security Team"
    )

    licence_type = models.CharField(
        choices=LicenceType.choices, max_length=1, default="", verbose_name="Licence Type"
    )

    supporting_documents = models.ManyToManyField("web.File")


class NuclearMaterialApplicationGoods(models.Model):
    import_application = models.ForeignKey(
        "web.ImportApplication", on_delete=models.CASCADE, related_name="nuclear_goods"
    )
    commodity = models.ForeignKey(
        "web.Commodity",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Commodity Code",
    )

    goods_description = models.CharField(
        max_length=4096, verbose_name="Goods Description (Including UN Number)"
    )
    # CHIEF spec:
    # 9(n).9(m) decimal field with up to n digits before the decimal point and up to m digits after.
    # quantityIssued 9(11).9(3)
    quantity_amount = models.DecimalField(
        max_digits=14, decimal_places=3, verbose_name="Quantity", null=True, blank=True
    )
    # value issued: 9(10).9(2)

    quantity_unit = models.ForeignKey("web.Unit", on_delete=models.PROTECT, related_name="+")
    unlimited_quantity = models.BooleanField(verbose_name="Unlimited Quantity", default=False)

    # Original values from applicant that cannot be overritten by the case officer
    goods_description_original = models.CharField(max_length=4096)
    quantity_amount_original = models.DecimalField(
        max_digits=14, decimal_places=3, null=True, blank=True
    )

    def __str__(self):
        return f"{self.import_application} - " f"{self.commodity} - " f"{self.quantity_amount} - "
