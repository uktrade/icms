from django.db import models

from .export import ExportApplication, ExportBase


class CertificateOfManufactureApplication(ExportBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    is_pesticide_on_free_sale_uk = models.BooleanField(null=True)
    is_manufacturer = models.BooleanField(null=True)
    product_name = models.CharField(max_length=1000, null=True)
    chemical_name = models.CharField(max_length=500, null=True)
    manufacturing_process = models.TextField(max_length=4000, null=True)
