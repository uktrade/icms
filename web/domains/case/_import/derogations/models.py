from django.db import models

from web.domains.file.models import File
from web.models.shared import YesNoNAChoices, at_least_0

from ..models import ChecklistBase, ImportApplication, ImportApplicationType


class DerogationsApplication(ImportApplication):
    class Unit(models.TextChoices):
        KG = ("kilos", "kilos")

    PROCESS_TYPE = ImportApplicationType.ProcessTypes.DEROGATIONS

    contract_sign_date = models.DateField(verbose_name="Contract Sign Date", null=True)
    contract_completion_date = models.DateField(verbose_name="Contract Completion Date", null=True)

    explanation = models.CharField(
        max_length=4096,
        null=True,
        verbose_name="Provide details of why this is a pre-existing contract",
    )

    # Goods
    commodity_code = models.CharField(
        max_length=40,
        null=True,
        verbose_name="Commodity Code",
        help_text=(
            "It is the responsibility of the applicant to ensure that the commodity code in"
            " this box is correct. If you are unsure of the correct commodity code,"
            " consult the HM Revenue and Customs Integrated Tariff Book, Volume 2,"
            " which is available from the Stationery Office. If you are still in doubt,"
            " contact the Classification Advisory Service on (01702) 366077."
        ),
    )

    goods_description = models.CharField(
        max_length=4096,
        null=True,
        verbose_name="Goods Description",
        help_text="Details of the goods that are subject to the contract notification",
    )

    quantity = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, validators=[at_least_0]
    )

    unit = models.CharField(max_length=40, null=True, verbose_name="Unit", choices=Unit.choices)

    value = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        validators=[at_least_0],
        verbose_name="Value (euro CIF)",
    )

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")


class DerogationsChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        DerogationsApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    supporting_document_received = models.CharField(
        max_length=10,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Supporting documentation received?",
    )
