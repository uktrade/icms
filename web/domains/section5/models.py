from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from web.models.mixins import Archivable
from web.models.shared import ArchiveReasonChoices


class Section5AuthorityManager(models.Manager):
    def currently_active(self):
        today = timezone.now().date()

        return self.filter(is_active=True, start_date__lte=today, end_date__gte=today)


class Section5Authority(models.Model):
    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, "Manual"), (SEARCH, "Search"))

    objects = Section5AuthorityManager()

    is_active = models.BooleanField(blank=False, null=False, default=True)
    reference = models.CharField(
        max_length=100,
        blank=False,
        null=True,
        help_text="Section 5 Authority reference. Example format: '14/A/D/0001'.",
    )
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=300, blank=False, null=True)
    address_entry_type = models.CharField(max_length=10, blank=False, null=True)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)
    further_details = models.CharField(max_length=4000, blank=True, null=True)
    linked_offices = models.ManyToManyField("web.Office")
    importer = models.ForeignKey(
        "web.Importer",
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="section5_authorities",
    )
    files = models.ManyToManyField("web.File")
    clauses = models.ManyToManyField("Section5Clause", through="ClauseQuantity")
    archive_reason = ArrayField(
        models.CharField(max_length=20, choices=ArchiveReasonChoices.choices),
        size=4,
        blank=True,
        null=True,
    )
    other_archive_reason = models.TextField(null=True, blank=True, verbose_name="Other")


class Section5Clause(Archivable, models.Model):
    clause = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", blank=True, null=True
    )

    class Meta:
        ordering = ("clause",)

    def __str__(self):
        return self.clause


class ClauseQuantity(models.Model):
    section5authority = models.ForeignKey("web.Section5Authority", on_delete=models.PROTECT)
    section5clause = models.ForeignKey("web.Section5Clause", on_delete=models.PROTECT)

    quantity = models.IntegerField(blank=True, null=True)
    infinity = models.BooleanField(default=False)
