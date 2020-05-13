from django.db import models
from web.models.mixins import Archivable


class Country(models.Model):
    SOVEREIGN_TERRITORY = 'SOVEREIGN_TERRITORY'
    SYSTEM = 'SYSTEM'

    TYPES = ((SOVEREIGN_TERRITORY, 'Sovereign Territory'), (SYSTEM, 'System'))

    name = models.CharField(max_length=4000, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    type = models.CharField(max_length=30,
                            choices=TYPES,
                            blank=False,
                            null=False)
    commission_code = models.CharField(max_length=20, blank=False, null=False)
    hmrc_code = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        if self.id:
            return f'Country ({self.name})'
        else:
            return 'Country (new) '

    @property
    def name_slug(self):
        return self.name.lower().replace(' ', '_')

    class Meta:
        ordering = ('name', )


class CountryGroup(models.Model):
    name = models.CharField(max_length=4000, blank=False, null=False)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    countries = models.ManyToManyField(Country,
                                       blank=True,
                                       related_name='country_groups')

    def __str__(self):
        if self.id:
            return f'Country Group ({self.name})'
        else:
            return 'Country Group (new) '

    class Meta:
        ordering = ('name', )


class CountryTranslationSet(Archivable, models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    def __str__(self):
        if self.id:
            return f'Country Translation Set ({self.name})'
        else:
            return 'Country Translation Set (new) '


class CountryTranslation(models.Model):
    translation = models.CharField(max_length=150, blank=False, null=False)
    country = models.ForeignKey(Country,
                                on_delete=models.CASCADE,
                                blank=False,
                                null=False)
    translation_set = models.ForeignKey(CountryTranslationSet,
                                        on_delete=models.CASCADE,
                                        blank=False,
                                        null=False)
