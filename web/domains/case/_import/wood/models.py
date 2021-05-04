from django.db import models

from web.domains.file.models import File

from ..models import ImportApplication


class WoodContractFile(File):
    reference = models.CharField(max_length=50, blank=False, null=False)
    contract_date = models.DateField(blank=False, null=False)


class WoodQuotaApplication(ImportApplication):
    PROCESS_TYPE = "WoodQuotaApplication"

    shipping_year = models.IntegerField(blank=False, null=True)

    # exporter
    exporter_name = models.CharField(max_length=100, blank=False, null=True)
    exporter_address = models.CharField(max_length=4000, blank=False, null=True)
    exporter_vat_nr = models.CharField(max_length=100, blank=False, null=True)

    #  goods
    commodity_code = models.CharField(max_length=40, blank=False, null=True)
    goods_description = models.CharField(max_length=100, blank=False, null=True)
    goods_qty = models.DecimalField(blank=False, null=True, max_digits=9, decimal_places=2)
    goods_unit = models.CharField(max_length=40, blank=False, null=True)

    # misc
    additional_comments = models.CharField(max_length=4000, blank=True, null=True)

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")

    #  contracts/pre-contracts
    contract_documents = models.ManyToManyField(WoodContractFile, related_name="+")


class WoodQuotaChecklist(models.Model):
    class Response(models.TextChoices):
        yes = ("yes", "Yes")
        no = ("no", "No")
        not_applicable = ("n/a", "N/A")

    import_application = models.ForeignKey(
        WoodQuotaApplication, on_delete=models.PROTECT, related_name="checklists"
    )

    sigl_wood_application_logged = models.BooleanField(
        default=False,
        verbose_name="Log on to SIGL Wood via this screen. Processing done on SIGL Wood.",
    )

    case_update = models.CharField(
        max_length=3,
        choices=Response.choices,
        null=True,
        verbose_name="Case update required from applicant?",
    )

    fir_required = models.CharField(
        max_length=3,
        choices=Response.choices,
        null=True,
        verbose_name="Further information request required?",
    )

    response_preparation = models.BooleanField(
        default=False,
        verbose_name="Response Preparation - approve/refuse the request, edit details if necessary",
    )

    validity_period_correct = models.CharField(
        max_length=3,
        choices=Response.choices,
        null=True,
        verbose_name="Validity period correct?",
    )

    endorsements_listed = models.CharField(
        max_length=3,
        choices=Response.choices,
        null=True,
        verbose_name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    )

    authorisation = models.BooleanField(
        default=False,
        verbose_name="Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved.",
    )
