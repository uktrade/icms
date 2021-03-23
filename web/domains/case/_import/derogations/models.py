from django.db import models

from ..models import ImportApplication


class DerogationsApplication(ImportApplication):
    PROCESS_TYPE = "DerogationsApplication"

    contract_sign_date = models.DateField(verbose_name="Contract Sign Date", null=True)
    contract_completion_date = models.DateField(verbose_name="Contract Completion Date", null=True)
    explanation = models.CharField(max_length=4096, null=True)
