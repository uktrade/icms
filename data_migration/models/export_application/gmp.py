from django.db import models

from data_migration.models.file import FileFolder
from web.models.shared import AddressEntryType

from .export import ExportApplication, ExportBase


class CertificateOfGoodManufacturingPracticeApplication(ExportBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    file_folder = models.ForeignKey(FileFolder, on_delete=models.CASCADE, related_name="gmp")
    brand_name = models.CharField(max_length=100, null=True)
    is_responsible_person = models.CharField(max_length=3, null=True)
    responsible_person_name = models.CharField(max_length=200, null=True)
    responsible_address_type = models.CharField(max_length=10, default=AddressEntryType.SEARCH)
    responsible_person_postcode = models.CharField(max_length=30, null=True)
    responsible_person_address = models.CharField(max_length=4000, null=True)
    responsible_person_country = models.CharField(max_length=3, null=True)
    is_manufacturer = models.CharField(max_length=3, null=True)
    manufacturer_name = models.CharField(max_length=200, null=True)
    manufacturer_address_type = models.CharField(max_length=10, default=AddressEntryType.SEARCH)
    manufacturer_postcode = models.CharField(max_length=30, null=True)
    manufacturer_address = models.CharField(max_length=4000, null=True)
    manufacturer_country = models.CharField(max_length=3, null=True)
    gmp_certificate_issued = models.CharField(max_length=10, null=True)
    auditor_accredited = models.CharField(max_length=3, null=True)
    auditor_certified = models.CharField(max_length=3, null=True)
