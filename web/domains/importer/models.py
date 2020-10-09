from django.db import models

from web.domains.office.models import Office
from web.domains.user.models import User
from web.models.mixins import Archivable


# TODO: explore if we should use the "direct foreign keys" for django-guardian
# for efficiency; see https://django-guardian.readthedocs.io/en/stable/userguide/performance.html
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

    is_active = models.BooleanField(blank=False, null=False, default=True)

    type = models.CharField(max_length=20, choices=TYPES, blank=False, null=False)

    # these are only set for organisations
    name = models.CharField(max_length=4000, blank=True, null=True)
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    eori_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="EORI Number",
        help_text="EORI number should include the GB prefix",
    )
    eori_number_ni = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="NI EORI Number"
    )
    region_origin = models.CharField(max_length=1, choices=REGIONS, blank=True, null=True)

    # only set for individuals
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="own_importers",
        verbose_name="Person",
    )

    # set for both
    comments = models.TextField(blank=True, null=True)
    offices = models.ManyToManyField(Office)

    # Having a main importer means importer is an agent
    main_importer = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="agents"
    )

    def is_agent(self):
        return self.main_importer is not None

    def is_organisation(self):
        return self.type == self.ORGANISATION

    def __str__(self):
        LABEL = ""
        if self.is_agent():
            LABEL = "Importer Agent"
        else:
            LABEL = "Importer"

        if self.id:
            return LABEL + " - " + self.display_name
        else:
            return LABEL

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

        # object-level permissions
        permissions = [
            ("is_contact_of_importer", "Is contact of this importer"),
            # NOTE: this is given on the "main importer" object, not on the "agent" object
            ("is_agent_of_importer", "Is agent of this importer"),
        ]
