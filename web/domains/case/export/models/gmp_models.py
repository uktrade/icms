from typing import final

from django.db import models

from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import AddressEntryType, YesNoChoices
from web.types import TypedTextChoices

from .common_models import ExportApplication


class CertificateOfGoodManufacturingPracticeApplicationABC(models.Model):
    class Meta:
        abstract = True

    class CertificateTypes(TypedTextChoices):
        ISO_22716 = ("ISO_22716", "ISO 22716")
        BRC_GSOCP = ("BRC_GSOCP", "BRC Global Standard for Consumer Products")

    class CountryType(TypedTextChoices):
        GB = ("GB", "Great Britain")
        NIR = ("NIR", "Northern Ireland")

    brand_name = models.CharField(
        max_length=100,
        verbose_name="Name of the brand",
        null=True,
        help_text="You must enter the cosmetic product brand name here",
    )

    # Responsible person fields
    is_responsible_person = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        default=None,
        verbose_name="Are you the responsible person as defined by Cosmetic Products Legislation as applicable in GB or NI?",
    )

    responsible_person_name = models.CharField(max_length=200, verbose_name="Name", null=True)

    responsible_person_address_entry_type = models.CharField(
        max_length=10,
        choices=AddressEntryType.choices,
        verbose_name="Address Type",
        default=AddressEntryType.SEARCH,
    )

    responsible_person_postcode = models.CharField(
        max_length=30,
        verbose_name="Postcode",
        null=True,
    )

    responsible_person_address = models.CharField(
        max_length=4000,
        verbose_name="Address",
        null=True,
    )

    responsible_person_country = models.CharField(
        max_length=3,
        choices=CountryType.choices,
        verbose_name="Country of Responsible Person",
        default=None,
        null=True,
    )

    # Manufacturer fields
    is_manufacturer = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        default=None,
        verbose_name="Are you the manufacturer of the cosmetic products?",
    )

    manufacturer_name = models.CharField(max_length=200, verbose_name="Name", null=True)

    manufacturer_address_entry_type = models.CharField(
        max_length=10,
        choices=AddressEntryType.choices,
        verbose_name="Address Type",
        default=AddressEntryType.SEARCH,
    )

    manufacturer_postcode = models.CharField(
        max_length=30,
        verbose_name="Postcode",
        null=True,
    )

    manufacturer_address = models.CharField(
        max_length=4000,
        verbose_name="Address",
        null=True,
    )

    manufacturer_country = models.CharField(
        max_length=3,
        choices=CountryType.choices,
        verbose_name="Country of Manufacture",
        null=True,
        default=None,
    )

    # Manufacturing certificates fields
    gmp_certificate_issued = models.CharField(
        max_length=10,
        null=True,
        choices=CertificateTypes.choices,
        verbose_name=(
            "Which valid certificate of Good Manufacturing Practice (GMP) has"
            " your cosmetics manufacturer been issued with?"
        ),
        default=None,
    )

    auditor_accredited = models.CharField(
        max_length=3,
        null=True,
        choices=YesNoChoices.choices,
        verbose_name=(
            "Is the auditor or auditing body who inspected and certified the"
            " manufacturing facility accredited according to ISO 17021 by a"
            " national accreditation body which is a member of the"
            " International Accreditation Forum?"
        ),
        default=None,
    )

    auditor_certified = models.CharField(
        max_length=3,
        null=True,
        choices=YesNoChoices.choices,
        verbose_name=(
            "Is the auditor or auditing body who inspected and certified the"
            " manufacturing facility accredited according to ISO 17065 by a"
            " national accreditation body which is a member of the"
            " International Accreditation Forum?"
        ),
        default=None,
    )

    supporting_documents = models.ManyToManyField("GMPFile")


@final
class CertificateOfGoodManufacturingPracticeApplication(  # type: ignore[misc]
    ExportApplication, CertificateOfGoodManufacturingPracticeApplicationABC
):
    PROCESS_TYPE = ProcessTypes.GMP
    IS_FINAL = True


class GMPFile(File):
    class Type(TypedTextChoices):
        # ISO_22716 file types
        ISO_22716 = ("ISO_22716", "ISO 22716")
        ISO_17021 = ("ISO_17021", "ISO 17021")
        ISO_17065 = ("ISO_17065", "ISO 17065")

        # BRC Global Standard for Consumer Products file types
        BRC_GSOCP = ("BRC_GSOCP", "BRC Global Standard for Consumer Products")

    file_type = models.CharField(max_length=10, choices=Type.choices)
