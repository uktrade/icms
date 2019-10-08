from web.models.mixins import Archivable
from django.db import models


class ProductLegislation(Archivable, models.Model):
    LABEL = 'Product Legislation'

    name = models.CharField(max_length=500, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    is_biocidal = models.BooleanField(blank=False, null=False, default=False)
    is_eu_cosmetics_regulation = models.BooleanField(blank=False,
                                                     null=False,
                                                     default=False)
    is_biocidal_claim = models.BooleanField(blank=False,
                                            null=False,
                                            default=False)

    @property
    def is_biocidal_yes_no(self):
        return 'Yes' if self.is_biocidal else 'No'

    @property
    def is_biocidal_claim_yes_no(self):
        return 'Yes' if self.is_biocidal_claim else 'No'

    @property
    def is_eu_cosmetics_regulation_yes_no(self):
        return 'Yes' if self.is_eu_cosmetics_regulation else 'No'

    def __str__(self):
        if self.id:
            return self.LABEL + ' - ' + self.name
        else:
            return self.LABEL

    class Meta:
        ordering = (
            '-is_active',
            'name',
        )
