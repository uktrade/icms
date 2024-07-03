from typing import final

from django.db import models

from web.domains.case._import.models import ChecklistBase, ImportApplication
from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import YesNoNAChoices, at_least_0


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

    requested_qty = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[at_least_0],
        verbose_name="Requested Quantity",
        help_text="This is the quantity that you will be importing against this export licence."
        " These values must add up to the total import quantity.",
    )


@final
class IronSteelApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.IRON_STEEL
    IS_FINAL = True

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
        "web.CommodityGroup",
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
        "web.Commodity",
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Commodity Code",
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

    supporting_documents = models.ManyToManyField("web.File", related_name="+")

    certificates = models.ManyToManyField("web.IronSteelCertificateFile", related_name="+")


class IronSteelChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        "web.IronSteelApplication", on_delete=models.PROTECT, related_name="checklist"
    )

    licence_category = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name=(
            "Do the export licence and application categories match, e.g. export licence SA1 and application SA1?"
        ),
    )
