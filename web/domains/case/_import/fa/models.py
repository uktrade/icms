from django.db import models

from web.domains.file.models import File
from web.models import ImportApplication


class ConstabularyEmail(models.Model):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"
    STATUSES = ((OPEN, "Open"), (CLOSED, "Closed"), (DRAFT, "Draft"))

    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="constabulary_emails"
    )

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30, blank=False, null=False, default=DRAFT)
    email_to = models.CharField(max_length=4000, blank=True, null=True)
    email_cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    email_subject = models.CharField(max_length=100, blank=False, null=True)
    email_body = models.TextField(max_length=4000, blank=False, null=True)
    email_response = models.TextField(max_length=4000, blank=True, null=True)
    email_sent_datetime = models.DateTimeField(blank=True, null=True)
    email_closed_datetime = models.DateTimeField(blank=True, null=True)
    attachments = models.ManyToManyField(File)

    @property
    def is_draft(self):
        return self.status == self.DRAFT
