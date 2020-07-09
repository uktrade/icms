from django.db import models
from web.domains.office.models import Office
from web.domains.team.models import BaseTeam
from web.models.mixins import Archivable

from .roles import EXPORTER_ROLES


class Exporter(Archivable, BaseTeam):
    role_list = EXPORTER_ROLES

    is_active = models.BooleanField(blank=False, null=False, default=True)
    name = models.CharField(max_length=4000, blank=False, null=False)
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    offices = models.ManyToManyField(Office)
    # Having a main exporter means exporter is an agent
    main_exporter = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="agents"
    )

    def is_agent(self):
        return self.main_exporter is not None

    def __str__(self):
        LABEL = ""
        if self.is_agent():
            LABEL = "Exporter Agent"
        else:
            LABEL = "Exporter"

        if self.id:
            return LABEL + " - " + (self.name or self.user.full_name)
        else:
            return LABEL

    class Meta:
        ordering = (
            "-is_active",
            "name",
        )
