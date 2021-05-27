from django.db import models

from web.domains.file.models import File

from ..models import ImportApplication


class OutwardProcessingTradeApplication(ImportApplication):
    PROCESS_TYPE = "OutwardProcessingTradeApplication"

    customs_office_name = models.CharField(
        max_length=100, null=True, verbose_name="Requested customs supervising office name"
    )

    customs_office_address = models.TextField(
        max_length=4000, null=True, verbose_name="Requested customs supervising office address"
    )

    rate_of_yield = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, verbose_name="Rate of yield (kg per garment)"
    )

    rate_of_yield_calc_method = models.TextField(
        max_length=4000, blank=True, null=True, verbose_name="Rate of yield calculation method"
    )

    last_export_day = models.DateField(
        null=True, help_text="Requested last day of authorised exportation."
    )

    reimport_period = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, verbose_name="Period for re-importation (months)"
    )

    nature_process_ops = models.TextField(
        max_length=4000, null=True, verbose_name="Nature of processing operations"
    )

    suggested_id = models.TextField(
        max_length=4000,
        null=True,
        verbose_name="Suggested means of identification",
        help_text="Enter the suggested means of identification of re-imported compensating products.",
    )

    # TODO: ICMLST-594 add Compensating Products

    # TODO: ICMLST-596 add Temporary Exported Goods

    # TODO: ICMLST-598 add Further Questions

    supporting_documents = models.ManyToManyField(File, related_name="+")
