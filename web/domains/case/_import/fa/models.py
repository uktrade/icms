from typing import TYPE_CHECKING, Union

from django.db import models

from web.domains.file.models import File
from web.domains.user.models import User
from web.models import ImportApplication
from web.models.shared import YesNoChoices

if TYPE_CHECKING:
    from django.db import QuerySet


class UserImportCertificate(File):
    """User imported certificates."""

    class CertificateType(models.TextChoices):
        firearms = ("firearms", "Firearms Certificate")
        registered = ("registered", "Registered Firearms Dealer Certificate")
        shotgun = ("shotgun", "Shotgun Certificate")

        @classmethod
        def registered_as_choice(cls) -> tuple[str, str]:
            return (cls.registered.value, cls.registered.label)  # type: ignore[attr-defined]

    reference = models.CharField(verbose_name="Certificate Reference", max_length=200)
    certificate_type = models.CharField(
        verbose_name="Certificate Type", choices=CertificateType.choices, max_length=200
    )
    constabulary = models.ForeignKey("web.Constabulary", on_delete=models.PROTECT)
    date_issued = models.DateField(verbose_name="Date Issued", null=True)
    expiry_date = models.DateField(verbose_name="Expiry Date", null=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class ImportContact(models.Model):
    LEGAL = "legal"
    NATURAL = "natural"
    ENTITIES = (
        (LEGAL, "Legal Person"),
        (NATURAL, "Natural Person"),
    )
    DEALER_CHOICES = (
        ("yes", "Yes"),
        ("no", "No"),
    )

    import_application = models.ForeignKey(ImportApplication, on_delete=models.CASCADE)
    entity = models.CharField(max_length=10, choices=ENTITIES)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    registration_number = models.CharField(max_length=200, null=True, blank=True)
    street = models.CharField(max_length=200, verbose_name="Street and Number")
    city = models.CharField(max_length=200, verbose_name="Town/City")
    postcode = models.CharField(max_length=200, null=True, blank=True)
    region = models.CharField(max_length=200, null=True, blank=True)
    country = models.ForeignKey("web.Country", on_delete=models.PROTECT, related_name="+")
    dealer = models.CharField(max_length=10, choices=DEALER_CHOICES, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}" if self.last_name else self.first_name


class SupplementaryInfoBase(models.Model):
    class Meta:
        abstract = True

    is_complete = models.BooleanField(default=False)
    completed_datetime = models.DateTimeField(null=True)

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )

    no_report_reason = models.CharField(
        max_length=4000,
        null=True,
        blank=True,
        verbose_name=(
            "You haven't provided any reports on imported firearms. You must provide a reason"
            " why no reporting is required before you confirm reporting complete."
        ),
    )


class SupplementaryReportBase(models.Model):
    class TransportType(models.TextChoices):
        AIR = ("air", "Air")
        RAIL = ("rail", "Rail")
        ROAD = ("road", "Road")
        SEA = ("sea", "Sea")

    class Meta:
        abstract = True

    transport = models.CharField(
        choices=TransportType.choices, max_length=4, blank=False, null=True
    )
    date_received = models.DateField(verbose_name="Date Received", null=True)

    bought_from = models.ForeignKey(
        ImportContact,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    created = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.pk} - {self.str_title()}"

    def str_title(self) -> str:
        return f"Supplementary Report {self.created:%d %B %Y}"

    def str_date_received(self):
        return f"{self.date_received:%d-%b-%Y}"

    def get_goods_certificates(self) -> "Union[QuerySet, list]":
        """Get the goods certificates associated with the firearm application."""
        raise NotImplementedError

    def get_report_firearms(
        self, is_manual: bool = False, is_upload: bool = False, is_no_firearm: bool = False
    ) -> "Union[QuerySet, list]":
        """Get the firearm details added to the supplementary report."""
        raise NotImplementedError


class SupplementaryReportFirearmBase(models.Model):
    class Meta:
        abstract = True

    serial_number = models.CharField(max_length=400, null=True)
    calibre = models.CharField(max_length=400, null=True)
    model = models.CharField(max_length=400, verbose_name="Make and Model", null=True)
    proofing = models.CharField(max_length=3, choices=YesNoChoices.choices, null=True, default=None)
    is_manual = models.BooleanField(default=False)
    is_upload = models.BooleanField(default=False)
    is_no_firearm = models.BooleanField(default=False)

    def get_description(self) -> str:
        """Get the description of the goods line."""
        raise NotImplementedError
