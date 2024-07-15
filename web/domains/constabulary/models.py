from django.db import models


class ConstabularyObjectPerms:
    """Return object permissions linked to the constabulary model.

    Implemented this way to resolve a circular import dependency.
    The permissions module needs to be able to import models so this ensures it can.
    """

    def __init__(self):
        self._perms = []

    def __iter__(self):
        if not self._perms:
            self._load()

        return iter(self._perms)

    def __eq__(self, other):
        """This is required to prevent django creating a new migration each time for this model."""

        return list(self) == list(other)

    def _load(self):
        from web.permissions import constabulary_object_permissions

        self._perms = constabulary_object_permissions


class Constabulary(models.Model):
    EAST_MIDLANDS = "EM"
    EASTERN = "ER"
    ISLE_OF_MAN = "IM"
    LONDON = "LO"
    NORTH_EAST = "NE"
    NORTH_WEST = "NW"
    ROYAL_ULSTER = "RU"
    SCOTLAND = "SC"
    SOUTH_EAST = "SE"
    SOUTH_WEST = "SW"
    WEST_MIDLANDS = "WM"

    REGIONS = (
        (EAST_MIDLANDS, "East Midlands"),
        (EASTERN, "Eastern"),
        (ISLE_OF_MAN, "Isle of Man"),
        (LONDON, "London"),
        (NORTH_EAST, "North East"),
        (NORTH_WEST, "North WEST"),
        (ROYAL_ULSTER, "Royal Ulster"),
        (SCOTLAND, "Scotland"),
        (SOUTH_EAST, "South East"),
        (SOUTH_WEST, "South West"),
        (WEST_MIDLANDS, "West Midlands"),
    )

    name = models.CharField(max_length=50, blank=False, null=False)
    region = models.CharField(max_length=3, choices=REGIONS, blank=False, null=False)
    email = models.EmailField(max_length=254, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    telephone_number = models.CharField(max_length=20, blank=True, null=True)

    @property
    def region_verbose(self):
        return dict(Constabulary.REGIONS)[self.region]

    def __str__(self):
        return self.name

    class Meta:
        ordering = (
            "-is_active",
            "name",
        )

        default_permissions: list[str] = []
        permissions = ConstabularyObjectPerms()
