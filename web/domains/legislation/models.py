from django.db import models

from web.models.mixins import Archivable


class ProductLegislation(Archivable, models.Model):
    name = models.CharField(max_length=500, verbose_name="Legislation Name")
    is_active = models.BooleanField(default=True)

    is_biocidal = models.BooleanField(
        default=False,
        verbose_name="Biocidal",
        help_text=(
            "Product type numbers and active ingredients must be entered"
            " by the applicant when biocidal legislation is selected"
        ),
    )

    is_eu_cosmetics_regulation = models.BooleanField(
        default=False,
        verbose_name="Cosmetics Regulation",
        help_text=(
            "A 'responsible person' statement may be added to the issued certificate"
            " schedule when the applicant selects EU Cosmetics Regulation legislation"
        ),
    )

    is_biocidal_claim = models.BooleanField(default=False, verbose_name="Biocidal Claim")
    gb_legislation = models.BooleanField(default=True, verbose_name="GB Legislation")
    ni_legislation = models.BooleanField(default=True, verbose_name="NI Legislation")

    @property
    def is_biocidal_yes_no(self):
        return "Yes" if self.is_biocidal else "No"

    @property
    def is_biocidal_claim_yes_no(self):
        return "Yes" if self.is_biocidal_claim else "No"

    @property
    def is_eu_cosmetics_regulation_yes_no(self):
        return "Yes" if self.is_eu_cosmetics_regulation else "No"

    @property
    def is_gb_legislation(self):
        return "Yes" if self.gb_legislation else "No"

    @property
    def is_ni_legislation(self):
        return "Yes" if self.ni_legislation else "No"

    def __str__(self):
        if self.id:
            return self.name
        else:
            return "Product Legislation (new)"

    class Meta:
        ordering = (
            "-is_active",
            "name",
        )
