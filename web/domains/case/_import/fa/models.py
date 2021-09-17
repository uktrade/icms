from django.db import models

from web.domains.file.models import File
from web.domains.user.models import User
from web.models import ImportApplication
from web.models.shared import YesNoChoices


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
    date_issued = models.DateField(verbose_name="Date Issued")
    expiry_date = models.DateField(verbose_name="Expiry Date")
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

    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
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


class SupplementaryInfo(models.Model):
    is_complete = models.BooleanField(default=False)
    completed_datetime = models.DateTimeField(null=True)

    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )

    no_report_reason = models.CharField(
        max_length=1000,
        null=True,
        verbose_name=(
            "You haven't provided any reports on imported firearms. You must provide a reason"
            " why no reporting is required before you confirm reporting complete."
        ),
    )


class SupplementaryReport(models.Model):
    class TransportType(models.TextChoices):
        AIR = ("air", "Air")
        RAIL = ("rail", "Rail")
        ROAD = ("road", "Road")
        SEA = ("sea", "Sea")

    supplementary_info = models.ForeignKey(
        SupplementaryInfo, related_name="reports", on_delete=models.CASCADE
    )
    transport = models.CharField(choices=TransportType.choices, max_length=4, blank=False)
    date_received = models.DateField(verbose_name="Date Received")

    bought_from = models.ForeignKey(
        ImportContact,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )

    created = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Supplementary Report {self.created:%d %B %Y}"

    def str_date_received(self):
        return f"{self.date_received:%d-%b-%Y}"


class SupplementaryReportFirearm(models.Model):

    # TODO: ICMSLST-960: Add FK for uploaded document
    # TODO: ICMSLST-961: Goods reference for firearm needs to be linked to this info

    report = models.ForeignKey(
        SupplementaryReport, related_name="firearms", on_delete=models.CASCADE
    )
    serial_number = models.CharField(max_length=20, null=True)
    calibre = models.CharField(max_length=20, null=True)
    model = models.CharField(max_length=20, verbose_name="Make and Model", null=True)
    proofing = models.CharField(max_length=3, choices=YesNoChoices.choices, null=True, default=None)


class FirearmApplicationBase(ImportApplication):
    class Meta:
        abstract = True

    supplementary_info = models.OneToOneField(
        SupplementaryInfo,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )
