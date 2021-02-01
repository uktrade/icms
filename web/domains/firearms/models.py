from django.db import models
from django.utils import timezone

from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.user.models import User
from web.models.mixins import Archivable, Sortable


class ActiveFirearmsAuthorityManager(models.Manager):
    def active(self):
        now = timezone.now()
        return self.filter(is_active=True).filter(start_date__lte=now).filter(end_date__gte=now)


class FirearmsAuthority(models.Model):
    DEACTIVATED_FIREARMS = "DEACTIVATED"
    FIREARMS = "FIREARMS"
    REGISTERED_FIREARMS_DEALER = "RFD"
    SHOTGUN = "SHOTGUN"

    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, "Manual"), (SEARCH, "Search"))

    CERTIFICATE_TYPES = (
        (DEACTIVATED_FIREARMS, "Deactivation Certificate"),
        (FIREARMS, "Firearms Certificate"),
        (REGISTERED_FIREARMS_DEALER, "Registered Firearms Dealer Certificate"),
        (SHOTGUN, "Shotgun Certificate"),
    )

    objects = ActiveFirearmsAuthorityManager()

    is_active = models.BooleanField(blank=False, null=False, default=True)
    reference = models.CharField(max_length=50, blank=False, null=True)
    certificate_type = models.CharField(
        max_length=20, choices=CERTIFICATE_TYPES, blank=False, null=True
    )
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=300, blank=False, null=True)
    address_entry_type = models.CharField(max_length=10, blank=False, null=True)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)
    further_details = models.CharField(max_length=4000, blank=True, null=True)
    issuing_constabulary = models.ForeignKey(
        Constabulary, on_delete=models.PROTECT, blank=False, null=True
    )
    linked_offices = models.ManyToManyField(Office)
    importer = models.ForeignKey(
        Importer,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="firearms_authorities",
    )
    files = models.ManyToManyField(File)


class FirearmsAct(Archivable, models.Model):
    act = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+", blank=True, null=True
    )

    class Meta:
        ordering = ("act",)

    def __str__(self):
        return self.act


class ActQuantity(models.Model):
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.PROTECT)
    firearmsact = models.ForeignKey(FirearmsAct, on_delete=models.PROTECT)

    quantity = models.IntegerField(blank=True, null=True)
    infinity = models.BooleanField(default=False)


class ObsoleteCalibreGroup(Archivable, Sortable, models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False)

    def __str__(self):
        if self.id:
            return f"Obsolete Calibre Group ({self.name})"
        else:
            return "Obsolete Calibre Group (new) "

    class Meta:
        ordering = ("order", "-is_active")


class ObsoleteCalibre(Archivable, models.Model):
    calibre_group = models.ForeignKey(
        ObsoleteCalibreGroup,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="calibres",
    )
    name = models.CharField(max_length=200, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False)

    def __str__(self):
        if self.id:
            return f"Obsolete Calibre ({self.name})"
        else:
            return "Obsolete Calibre (New) "

    @property
    def status(self):
        if not self.id:
            return "Pending"
        elif not self.is_active:
            return "Archived"
        else:
            return "Current"

    class Meta:
        ordering = ("order",)
