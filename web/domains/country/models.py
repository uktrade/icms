from django.db import models
from django.urls import reverse

from web.models.mixins import Archivable

from .managers import ApplicationCountryManager, UtilityCountryManager
from .types import CountryGroupName


class Country(models.Model):
    # Default manager.
    objects = models.Manager()
    # Custom Managers.
    app = ApplicationCountryManager()
    util = UtilityCountryManager()

    SOVEREIGN_TERRITORY = "SOVEREIGN_TERRITORY"
    SYSTEM = "SYSTEM"
    TYPES = ((SOVEREIGN_TERRITORY, "Sovereign Territory"), (SYSTEM, "System"))

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=["name", "is_active"], name="country_group_unique")
        ]

    name = models.CharField(max_length=4000, blank=False, null=False, unique=True)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    type = models.CharField(max_length=30, choices=TYPES, blank=False, null=False)
    commission_code = models.CharField(max_length=20, blank=False, null=False)
    hmrc_code = models.CharField(max_length=20, blank=False, null=False)
    overseas_region = models.ForeignKey(
        "web.OverseasRegion",
        blank=True,
        null=True,
        related_name="countries",
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.name

    @property
    def name_slug(self):
        return self.name.lower().replace(" ", "_")


class CountryGroup(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Group Name",
        choices=CountryGroupName.choices,
    )
    comments = models.CharField(
        max_length=4000, blank=True, null=True, verbose_name="Group Comments"
    )
    countries = models.ManyToManyField(
        "web.Country",
        blank=True,
        related_name="country_groups",
        limit_choices_to={"is_active": True},
    )

    def get_absolute_url(self):
        return reverse("country:group-view", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name} - ({self.countries.count()} countries)"

    class Meta:
        ordering = ("name",)


class CountryTranslationSet(Archivable, models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    def __str__(self):
        if self.id:
            return f"Country Translation Set ({self.name})"
        else:
            return "Country Translation Set (new) "

    class Meta:
        ordering = ("-is_active", "name")


class CountryTranslation(models.Model):
    translation = models.CharField(max_length=255, blank=False, null=False)
    country = models.ForeignKey(
        "web.Country",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        limit_choices_to={"is_active": True},
    )
    translation_set = models.ForeignKey(
        "web.CountryTranslationSet", on_delete=models.CASCADE, blank=False, null=False
    )


class OverseasRegion(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
