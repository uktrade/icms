from django.conf import settings
from django.db import models
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase

from web.models.mixins import Archivable


class ImporterObjectPerms:
    """Return object permissions linked to the importer model.

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
        from web.permissions import importer_object_permissions

        self._perms = importer_object_permissions


class ImporterManager(models.Manager):
    def agents(self):
        return self.filter(main_importer__isnull=False)


class Importer(Archivable, models.Model):
    # Regions
    INDIVIDUAL = "INDIVIDUAL"
    ORGANISATION = "ORGANISATION"
    TYPES = ((INDIVIDUAL, "Individual"), (ORGANISATION, "Organisation"))

    # Region Origins
    UK = None
    EUROPE = "E"
    NON_EUROPEAN = "O"
    REGIONS = ((UK, "UK"), (EUROPE, "Europe"), (NON_EUROPEAN, "Non-European"))

    objects = ImporterManager()

    is_active = models.BooleanField(blank=False, null=False, default=True)

    type = models.CharField(max_length=20, choices=TYPES, verbose_name="Entity Type")

    # name and registered_number are only set for organisations
    name = models.TextField(blank=True, default="", verbose_name="Organisation Name")
    registered_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Registered Number"
    )

    eori_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="EORI Number",
        help_text="EORI number should include the GB prefix",
    )
    region_origin = models.CharField(max_length=1, choices=REGIONS, blank=True, null=True)

    # only set for individuals
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="own_importers",
        verbose_name="Person",
        help_text=(
            "Search a user to link. Users returned are matched against first/last name,"  # /PS-IGNORE
            " email and title."
        ),
    )

    # set for both
    comments = models.TextField(blank=True, null=True)
    offices = models.ManyToManyField("web.Office")

    # Having a main importer means importer is an agent
    main_importer = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="agents"
    )

    def is_agent(self):
        return self.main_importer is not None

    def is_organisation(self):
        return self.type == self.ORGANISATION

    def __str__(self):
        if self.is_agent():
            return f"Agent - {self.display_name}"

        return self.display_name

    @property
    def display_name(self):
        if self.is_organisation():
            return self.name
        else:
            return self.user.full_name if self.user else "None"

    @property
    def status(self):
        return "Current" if self.is_active else "Archived"

    @property
    def entity_type(self):
        return dict(Importer.TYPES)[self.type]

    class Meta:
        ordering = (
            "-is_active",
            "name",
        )

        default_permissions: list[str] = []
        permissions = ImporterObjectPerms()


# Direct foreign key support for Django-Guardian
# https://django-guardian.readthedocs.io/en/stable/userguide/performance.html#direct-foreign-keys
class ImporterUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey("web.Importer", on_delete=models.CASCADE)


class ImporterGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey("web.Importer", on_delete=models.CASCADE)
