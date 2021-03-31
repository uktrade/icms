from django.db import models

from ..models import ImportApplication


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
