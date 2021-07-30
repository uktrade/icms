from django.db import models

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.commodity.models import Commodity, CommodityGroup
from web.domains.file.models import File
from web.models.shared import at_least_0


class IronSteelCertificateFile(File):
    reference = models.CharField(
        max_length=100,
        verbose_name="Export Certificate Reference",
        help_text="Enter your reference including prefixes, in the format of four characters followed by eight digits, e.g. KZGB12345678.",
    )

    total_qty = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[at_least_0],
        verbose_name="Total Quantity",
        help_text="This is the total quantity allowed by the export licence.",
    )

    # TODO: form validation: "Please ensure that the sum of export certificate
    # requested quantities equals the total quantity of imported goods."" (this
    # goes in submit validation)

    requested_qty = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[at_least_0],
        verbose_name="Requested Quantity",
        help_text="This is the quantity that you will be importing against this export licence."
        " These values must add up to the total import quantity.",
    )


class IronSteelApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.IRON_STEEL

    goods_cleared = models.BooleanField(
        null=True,
        verbose_name="Will the goods be cleared in another Member State of the European Union?",
        help_text="If yes, a paper licence will be issued.",
    )

    shipping_year = models.PositiveSmallIntegerField(
        null=True,
        verbose_name="Shipping Year",
        help_text=(
            "Date of shipment should be as shown on your export licence or"
            " other export document issued by the exporting country for"
            " goods covered by this application. The goods must be exported"
            " by 31 December. Shipment is considered to have taken place when"
            " the goods are loaded onto the exporting aircraft, vehicle or vessel."
        ),
    )

    # Goods
    category_commodity_group = models.ForeignKey(
        CommodityGroup,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Category",
        help_text=(
            "The category defines what commodities you are applying to import. This will be"
            " SA1 (coils) or SA3 (other flat products). Please see the guidance for further"
            " information regarding the coverage of the categories."
        ),
    )

    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Commodity Code",
        help_text=(
            "It is the responsibility of the applicant to ensure that the"
            " commodity code in this box is correct. If you are unsure of the"
            " correct commodity code, consult the HM Revenue and Customs"
            " Integrated Tariff Book, Volume 2, which is available from the"
            " Stationery Office. If you are still in doubt, contact the"
            " Classification Advisory Service on (01702) 366077."
        ),
    )

    goods_description = models.CharField(
        max_length=100,
        null=True,
        verbose_name="Goods Description",
        help_text="Please describe the goods in no more than five (5) words.",
    )

    quantity = models.DecimalField(
        null=True,
        max_digits=9,
        decimal_places=2,
        validators=[at_least_0],
    )

    supporting_documents = models.ManyToManyField(File, related_name="+")

    certificates = models.ManyToManyField(IronSteelCertificateFile, related_name="+")
