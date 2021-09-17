from django.db import models

from web.domains.case._import.models import ImportApplication
from web.domains.commodity.models import Commodity
from web.domains.file.models import File
from web.flow.models import ProcessTypes


class PriorSurveillanceContractFile(File):
    class Type(models.TextChoices):
        PRO_FORMA_INVOICE = ("pro_forma_invoice", "Pro-forma Invoice")
        SUPPLY_CONTRACT = ("supply_contract", "Supply Contract")

    file_type = models.CharField(max_length=32, choices=Type.choices)


class PriorSurveillanceApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.SPS

    customs_cleared_to_uk = models.BooleanField(
        null=True,
        verbose_name="Will the goods be customs cleared into the UK?",
        help_text="If no, a paper licence will be issued for clearance in another EU Member State.",
    )

    # goods
    commodity = models.ForeignKey(
        Commodity,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Commodity Code",
        help_text=(
            "It is the responsibility of the applicant to ensure that the"
            " commodity code in this box is correct. If you are unsure of the"
            " correct commodity code, consult the HM Revenue & Customs at"
            " classification.enquiries@hmrc.gsi.gov.uk or use the online trade"
            " tariff https://www.gov.uk/trade-tariff/sections."
        ),
    )

    quantity = models.PositiveIntegerField(
        null=True,
        verbose_name="Quantity",
        help_text=(
            "Please note that maximum allocations apply. Please check the"
            " guidance to ensure that you do not apply for more than is allowable."
        ),
    )

    value_gbp = models.PositiveIntegerField(
        null=True,
        verbose_name="Value (GBP/£)",
        help_text=(
            "Round up to the nearest GBP. Do not enter decimal points, commas"
            " or any other punctuation in this box. The entered value will be"
            " automatically converted to EUR."
        ),
    )

    value_eur = models.PositiveIntegerField(null=True, verbose_name="Value (EUR/€)")

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")

    contract_file = models.OneToOneField(
        PriorSurveillanceContractFile, on_delete=models.PROTECT, null=True, related_name="+"
    )
