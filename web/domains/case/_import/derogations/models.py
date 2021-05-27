from django.db import models

from web.domains.file.models import File

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

    #  supporting documents
    supporting_documents = models.ManyToManyField(File, related_name="+")


# FIXME: Refactor to use base class
class DerogationsChecklist(models.Model):
    class Response(models.TextChoices):
        yes = ("yes", "Yes")
        no = ("no", "No")
        not_applicable = ("n/a", "N/A")

    import_application = models.ForeignKey(
        DerogationsApplication, on_delete=models.PROTECT, related_name="checklists"
    )

    supporting_document_received = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Supporting documentation received?",
    )

    case_update = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Case update required from applicant?",
    )

    fir_required = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Further information request required?",
    )

    response_preparation = models.BooleanField(
        default=False,
        verbose_name="Response Preparation - approve/refuse the request, edit details if necessary",
    )

    validity_period_correct = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Validity period correct?",
    )

    endorsements_listed = models.CharField(
        max_length=10,
        choices=Response.choices,
        blank=True,
        null=True,
        verbose_name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    )

    authorisation = models.BooleanField(
        default=False,
        verbose_name="Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved.",
    )
