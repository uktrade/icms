from django.db import models

from web.domains.file.models import File
from web.domains.user.models import User
from web.models import ImportApplication


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


class SupplementaryReport(models.Model):
    # TODO ICMSLST-954: Use this model

    class TransportType(models.TextChoices):
        AIR = ("air", "Air")
        RAIL = ("rail", "Rail")
        ROAD = ("road", "Road")
        SEA = ("sea", "Sea")

    transport = models.CharField(choices=TransportType.choices, max_length=4, blank=False)
    date_received = models.DateField(verbose_name="Date Received")

    bought_from = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )


class SupplementaryInfo(models.Model):
    import_application = models.OneToOneField(
        ImportApplication, on_delete=models.PROTECT, related_name="supplementary_info"
    )
    is_complete = models.BooleanField(default=False)
    completed_datetime = models.DateTimeField(null=True)

    completed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
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

    reports = models.ManyToManyField(SupplementaryReport)
