from django.db import models

from web.permissions import all_permissions
from web.types import TypedTextChoices


class UniqueReference(models.Model):
    class Prefix(TypedTextChoices):
        # Import application case reference
        IMPORT_APP = "IMA"

        # Import application licence document reference
        IMPORT_LICENCE_DOCUMENT = "ILD"

        # Export certificate document reference
        EXPORT_CERTIFICATE_DOCUMENT_CFS = "CFS"
        EXPORT_CERTIFICATE_DOCUMENT_COM = "COM"
        EXPORT_CERTIFICATE_DOCUMENT_GMP = "GMP"

        # Export application case reference
        EXPORT_APP_GA = "GA"
        EXPORT_APP_CA = "CA"

        # Mailshot
        MAILSHOT = "MAIL"

        # Import Access Request
        IMP_ACCESS_REQ = "IAR"

        # Export Access Request
        EXP_ACCESS_REQ = "EAR"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["prefix", "year", "reference"], name="reference_unique")
        ]

    def __str__(self):
        return f"UniqueReference(prefix={self.prefix!r}, year={self.year!r}, reference={self.reference!r})"

    prefix = models.CharField(max_length=8, choices=Prefix.choices)

    # this is null for importer/exporter access requests and mailshots
    year = models.IntegerField(null=True)

    # incrementing number for each prefix/year combination, starting from 1
    reference = models.IntegerField()


class GlobalPermission(models.Model):
    """Contains global permissions.

    None of these should ever be assigned to users directly; all permissions
    should be granted to users by assigning the users to one or more groups.

    See
    https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model.
    """

    class Meta:
        managed = False
        default_permissions: list[str] = []

        permissions = all_permissions
