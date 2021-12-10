from django.db import models


# TODO: ICMSLST-1175 Rename CaseReference
class CaseReference(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["prefix", "year", "reference"], name="reference_unique")
        ]

    def __str__(self):
        return f"CaseReference(prefix={self.prefix!r}, year={self.year!r}, reference={self.reference!r})"

    # e.g. "IMA" for import applications
    prefix = models.CharField(max_length=8)

    # this is null for importer/exporter access requests and mailshots
    year = models.IntegerField(null=True)

    # incrementing number for each prefix/year combination, starting from 1
    reference = models.IntegerField()
