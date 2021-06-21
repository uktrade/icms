from django.db import models


class CaseReference(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["prefix", "year", "reference"], name="reference_unique")
        ]

    # e.g. "IMA" for import applications
    prefix = models.CharField(max_length=8)

    # this is null for importer/exporter access requests
    year = models.IntegerField(null=True)

    # incrementing number for each prefix/year combination, starting from 1
    reference = models.IntegerField()
