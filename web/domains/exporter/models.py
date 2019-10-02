from django.db import models
from web.domains.office.models import Office
from web.domains.team.models import BaseTeam
from web.models.mixins import Archivable


class Exporter(Archivable, BaseTeam):

    is_active = models.BooleanField(blank=False, null=False, default=True)
    name = models.CharField(max_length=4000, blank=False, null=False)
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    offices = models.ManyToManyField(Office)
    # Having a main exporter means exporter is an agent
    main_exporter = models.ForeignKey("self",
                                      on_delete=models.SET_NULL,
                                      blank=True,
                                      null=True,
                                      related_name='agents')

    def is_agent(self):
        return self.main_exporter is not None

    class Meta:
        ordering = (
            '-is_active',
            'name',
        )
