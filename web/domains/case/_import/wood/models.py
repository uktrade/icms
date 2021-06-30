from django.db import models

from web.domains.file.models import File

from ..models import ChecklistBase, ImportApplication, ImportApplicationType


class WoodContractFile(File):
    reference = models.CharField(
        max_length=100,
        help_text="Enter the reference number of the contract/pre-contract between the importer and exporter.",
    )

    contract_date = models.DateField(
        help_text="Enter the date of the contract/pre-contract between the importer and exporter."
    )


class WoodQuotaApplication(ImportApplication):
    PROCESS_TYPE = ImportApplicationType.ProcessTypes.WOOD

    shipping_year = models.IntegerField(null=True)

    # exporter
    exporter_name = models.CharField(max_length=100, null=True)
    exporter_address = models.CharField(max_length=4000, null=True)
    exporter_vat_nr = models.CharField(max_length=100, null=True)

    #  goods
    commodity_code = models.CharField(max_length=40, null=True)
    goods_description = models.CharField(max_length=100, null=True)
    goods_qty = models.DecimalField(null=True, max_digits=9, decimal_places=2)
    goods_unit = models.CharField(max_length=40, null=True)

    # misc
    additional_comments = models.CharField(max_length=4000, blank=True, null=True)

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")

    #  contracts/pre-contracts
    contract_documents = models.ManyToManyField(WoodContractFile, related_name="+")


class WoodQuotaChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        WoodQuotaApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    sigl_wood_application_logged = models.BooleanField(
        default=False,
        verbose_name="Log on to SIGL Wood via this screen. Processing done on SIGL Wood.",
    )
