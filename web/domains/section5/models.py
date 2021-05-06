from django.db import models

from web.domains.file.models import File
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.models.mixins import Archivable


class Section5Authority(models.Model):
    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, "Manual"), (SEARCH, "Search"))

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
    linked_offices = models.ManyToManyField(Office)
    importer = models.ForeignKey(
        Importer,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="section5_authorities",
    )
    files = models.ManyToManyField(File)
    clauses = models.ManyToManyField("Section5Clause", through="ClauseQuantity")


class Section5Clause(Archivable, models.Model):
    clause = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+", blank=True, null=True
    )

    class Meta:
        ordering = ("clause",)

    def __str__(self):
        return self.clause


class ClauseQuantity(models.Model):
    section5authority = models.ForeignKey(Section5Authority, on_delete=models.PROTECT)
    section5clause = models.ForeignKey(Section5Clause, on_delete=models.PROTECT)

    quantity = models.IntegerField(blank=True, null=True)
    infinity = models.BooleanField(default=False)
