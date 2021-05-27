from django.db import models

from web.domains.file.models import File

from ..models import ChecklistBase, ImportApplication


class DerogationsApplication(ImportApplication):
    PROCESS_TYPE = "DerogationsApplication"

    contract_sign_date = models.DateField(verbose_name="Contract Sign Date", null=True)
    contract_completion_date = models.DateField(verbose_name="Contract Completion Date", null=True)
    explanation = models.CharField(max_length=4096, null=True)
    commodity_code = models.CharField(max_length=40, blank=False, null=True)
    goods_description = models.CharField(max_length=4096, null=True)
    quantity = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    unit = models.CharField(max_length=40, blank=False, null=True)
    value = models.DecimalField(max_digits=9, decimal_places=2, null=True)

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")


class DerogationsChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        DerogationsApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    supporting_document_received = models.CharField(
        max_length=10,
        choices=ChecklistBase.Response.choices,
        null=True,
        verbose_name="Supporting documentation received?",
    )
