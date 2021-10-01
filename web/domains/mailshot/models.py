from django.db import models

from web.domains.file.models import File
from web.domains.user.models import User


class Mailshot(models.Model):
    class Statuses(models.TextChoices):
        DRAFT = ("DRAFT", "Draft")
        PUBLISHED = ("PUBLISHED", "Published")
        RETRACTED = ("RETRACTED", "Retracted")
        CANCELLED = ("CANCELLED", "Cancelled")

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default=Statuses.DRAFT, choices=Statuses.choices)

    title = models.CharField(
        max_length=200,
        null=True,
        help_text="The mailshot title will appear in the recipient's workbasket.",
    )

    description = models.CharField(max_length=4000, null=True)

    is_email = models.BooleanField(
        verbose_name="Send Emails",
        default=True,
        help_text=(
            "Optionally send emails to the selected recipients. Note that uploaded"
            " documents will not be attached to the email."
        ),
    )

    email_subject = models.CharField(verbose_name="Email Subject", max_length=200)
    email_body = models.CharField(verbose_name="Email Body", max_length=4000, null=True)

    is_retraction_email = models.BooleanField(default=True)
    retract_email_subject = models.CharField(max_length=78, blank=False, null=True)
    retract_email_body = models.CharField(max_length=4000, blank=False, null=True)

    is_to_importers = models.BooleanField(default=False)
    is_to_exporters = models.BooleanField(default=False)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    create_datetime = models.DateTimeField(auto_now_add=True)

    published_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    published_datetime = models.DateTimeField(null=True)

    retracted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    retracted_datetime = models.DateTimeField(null=True)

    documents = models.ManyToManyField(File, related_name="+")

    @property
    def started(self):
        if self.create_datetime:
            return self.create_datetime.strftime("%d %b %Y %H:%M")

    @property
    def published(self):
        if self.published_datetime:
            return self.published_datetime.strftime("%d %b %Y %H:%M")

    @property
    def retracted(self):
        if self.retracted_datetime:
            return self.retracted_datetime.strftime("%d %b %Y %H:%M")

    @property
    def status_verbose(self):
        return self.get_status_display()

    def __str__(self):
        if self.pk:
            return f"Mailshot ({self.pk})"
        else:
            return "Mailshot (New)"

    class Meta:
        ordering = ("-pk",)
