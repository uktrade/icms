from django.db import models

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.file.models import File


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

    # TODO: add other fields

    supporting_documents = models.ManyToManyField(File, related_name="+")
