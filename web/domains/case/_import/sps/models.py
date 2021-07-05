from django.db import models

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.file.models import File


class PriorSurveillanceContractFile(File):
    class Type(models.TextChoices):
        PRO_FORMA_INVOICE = ("pro_forma_invoice", "Pro-forma Invoice")
        SUPPLY_CONTRACT = ("supply_contract", "Supply Contract")

    file_type = models.CharField(max_length=32, choices=Type.choices)


class PriorSurveillanceApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.SPS

    # TODO: add other fields

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")

    contract_file = models.OneToOneField(
        PriorSurveillanceContractFile, on_delete=models.PROTECT, null=True, related_name="+"
    )
