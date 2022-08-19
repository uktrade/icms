from typing import final

from django.db import models

from web.domains.commodity.models import Commodity
from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import YesNoChoices, YesNoNAChoices, at_least_0

from ..models import ChecklistBase, ImportApplication


@final
class DerogationsApplication(ImportApplication):
    class Unit(models.TextChoices):
        KG = ("kilos", "kilos")

    class SyrianRequestPurpose(models.TextChoices):
        HUMANITARIAN_CONCERNS = ("HC", "Humanitarian concerns")
        PROVISION_OF_SERVICES = ("POS", "Assisting in the provision of basic services")
        RESTORE_ECONOMIC_ACTIVITY = ("REA", "Reconstruction or restoring economic activity")
        OTHER_CIV_PURPOSE = ("OCP", "Other civilian purposes")

    PROCESS_TYPE = ProcessTypes.DEROGATIONS
    IS_FINAL = True

    contract_sign_date = models.DateField(
        verbose_name="Contract Sign Date",
        null=True,
        help_text=(
            "Date upon which the contract was signed. Please check the relevant Notice to"
            " Importers or Guidance that these dates are within the derogation period allowed.",
        ),
    )
    contract_completion_date = models.DateField(
        verbose_name="Contract Completion Date",
        null=True,
        help_text=(
            "Date upon which the contract will be completed. A copy of the contract"
            " is required as proof. Please check the relevant Notice to Importers"
            " or Guidance that these dates are within the derogation period allowed."
        ),
    )

    explanation = models.CharField(
        max_length=4096,
        null=True,
        verbose_name="Provide details of why this is a pre-existing contract",
        help_text="A copy of the contract is required as proof.",
    )

    # Goods
    commodity = models.ForeignKey(
        Commodity,
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
        verbose_name="Value (GBP)",
    )

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")

    # Further details section (for Syria)
    entity_consulted_name = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=(
            "Provide the name of the person, entity or body designated by the"
            " Syrian National Coalition for Opposition and Revolutionary Forces"
            " that was consulted"
        ),
    )

    activity_benefit_anyone = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        blank=True,
        verbose_name=(
            "Do the activities concerned benefit anyone listed in Article 2 of"
            " EU Regulations 2580/2001 and 881/2002 or Article 14 of EU"
            " Regulation 36/2012?"
        ),
    )

    purpose_of_request = models.CharField(
        max_length=3,
        choices=SyrianRequestPurpose.choices,
        null=True,
        blank=True,
        verbose_name=(
            "Purpose of the request and how it provides assistance to the"
            " Syrian civilian population"
        ),
    )

    civilian_purpose_details = models.CharField(
        max_length=4096,
        null=True,
        blank=True,
        verbose_name="Provide details of the civilian purpose",
    )


class DerogationsChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        DerogationsApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    supporting_document_received = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Supporting documentation received?",
    )

    # Optional syria fields
    sncorf_consulted = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Syria National Coalition for Opposition and Revolutionary Forces (SNCORF) consulted?",
    )

    sncorf_response_within_30_days = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="SNCORF response within 30 days of consultation?",
    )

    beneficiaries_not_on_list = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Beneficiaries not on Syria sanctions list?",
    )

    request_purpose_confirmed = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Purpose of Syria request confirmed?",
    )
