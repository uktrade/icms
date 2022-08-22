from django.db import models

from .export import ExportApplication, ExportBase


class CertificateOfFreeSaleApplication(ExportBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    schedule_xml = models.TextField(null=True)
