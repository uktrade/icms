from typing import final

from django.db import models

from web.flow.models import ProcessTypes

from .common_models import ExportApplication


class CertificateOfManufactureApplicationABC(models.Model):
    class Meta:
        abstract = True

    is_pesticide_on_free_sale_uk = models.BooleanField(null=True)
    is_manufacturer = models.BooleanField(null=True)

    product_name = models.CharField(max_length=1000, blank=False, null=True)
    chemical_name = models.CharField(max_length=500, blank=False, null=True)
    manufacturing_process = models.TextField(max_length=4000, blank=False, null=True)


@final
class CertificateOfManufactureApplication(  # type: ignore[misc]
    ExportApplication, CertificateOfManufactureApplicationABC
):
    PROCESS_TYPE = ProcessTypes.COM
    IS_FINAL = True
