from django.db import models

from web.domains.file.models import File

from ..models import ImportApplication


class SanctionsAndAdhocApplication(ImportApplication):
    PROCESS_TYPE = "SanctionsAndAdhocApplication"

    exporter_name = models.CharField(max_length=4096, blank=True, null=True)
    exporter_address = models.CharField(max_length=4096, blank=True, null=True)
    supporting_documents = models.ManyToManyField(File)


class SanctionsAndAdhocApplicationGoods(models.Model):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    commodity_code = models.CharField(max_length=40, blank=False, null=True)
    goods_description = models.CharField(max_length=4096)
    quantity_amount = models.DecimalField(max_digits=9, decimal_places=2)
    value = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return (
            f"{self.import_application} - "
            f"{self.commodity_code} - "
            f"{self.quantity_amount} - "
            f"{self.value}"
        )


class SanctionEmailMessage(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"
    STATUSES = ((OPEN, "Open"), (CLOSED, "Closed"), (DRAFT, "Draft"))

    is_active = models.BooleanField(default=True)
    application = models.ForeignKey(
        SanctionsAndAdhocApplication,
        on_delete=models.PROTECT,
        related_name="sanction_emails",
    )
    status = models.CharField(max_length=30, default=DRAFT)

    to = models.CharField(max_length=4000, blank=True, null=True)
    cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    subject = models.CharField(max_length=100, blank=False, null=True)
    body = models.TextField(max_length=4000, blank=False, null=True)
    response = models.TextField(max_length=4000, blank=True, null=True)
    sent_datetime = models.DateTimeField(blank=True, null=True)
    closed_datetime = models.DateTimeField(blank=True, null=True)
    attachments = models.ManyToManyField(File)

    @property
    def is_draft(self):
        return self.status == self.DRAFT
