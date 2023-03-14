from typing import final

from django.db import models

from web.domains.file.models import File
from web.flow.models import ProcessTypes

from ..models import ChecklistBase, ImportApplication

WOOD_UNIT_CHOICES = [(x, x) for x in ["cubic metres"]]


class WoodContractFile(File):
    reference = models.CharField(
        max_length=100,
        help_text="Enter the reference number of the contract/pre-contract between the importer and exporter.",
    )

    contract_date = models.DateField(
        help_text="Enter the date of the contract/pre-contract between the importer and exporter."
    )


@final
class WoodQuotaApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.WOOD
    IS_FINAL = True

    shipping_year = models.IntegerField(null=True)

    # exporter
    exporter_name = models.CharField(max_length=100, null=True)
    exporter_address = models.CharField(max_length=4000, null=True, verbose_name="Exporter address")
    exporter_vat_nr = models.CharField(
        max_length=100, null=True, verbose_name="Exporter VAT number"
    )

    #  goods
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

    goods_description = models.CharField(max_length=100, null=True)
    goods_qty = models.DecimalField(
        null=True, max_digits=9, decimal_places=2, verbose_name="Quantity"
    )
    goods_unit = models.CharField(
        max_length=40, null=True, verbose_name="Unit", choices=WOOD_UNIT_CHOICES
    )

    # misc
    additional_comments = models.CharField(
        max_length=4000, blank=True, null=True, verbose_name="Additional Comments"
    )

    #  supporting documents
    supporting_documents = models.ManyToManyField("web.File", related_name="+")

    #  contracts/pre-contracts
    contract_documents = models.ManyToManyField("web.WoodContractFile", related_name="+")


class WoodQuotaChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        "web.WoodQuotaApplication", on_delete=models.PROTECT, related_name="checklist"
    )

    sigl_wood_application_logged = models.BooleanField(
        default=False,
        verbose_name="Log on to SIGL Wood via this screen. Processing done on SIGL Wood.",
    )
