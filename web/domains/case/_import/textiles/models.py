from typing import final

from django.db import models

from web.domains.case._import.models import ChecklistBase, ImportApplication
from web.domains.commodity.models import Commodity, CommodityGroup
from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import at_least_0


@final
class TextilesApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.TEXTILES
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

    category_commodity_group = models.ForeignKey(
        CommodityGroup,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Category",
        help_text="The category defines what commodities you are applying to import.",
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

    category_licence_description = models.CharField(
        null=True,
        max_length=4000,
        verbose_name="Category Description",
        help_text=(
            "By default, this is the category description. You may need to"
            " alter the description to a shorter form in order for it to"
            " display correctly on the licence."
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
        verbose_name="Quantity",
        help_text=(
            "Please note that maximum allocations apply. Please check the"
            " guidance to ensure that you do not apply for more than is allowable."
        ),
        validators=[at_least_0],
    )

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")


class TextilesChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        TextilesApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    within_maximum_amount_limit = models.BooleanField(
        default=False,
        verbose_name=(
            "Check amount to be imported is within the maximum amount limits"
            " for the category and country requested."
        ),
    )
