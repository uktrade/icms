from django.db import models
from web.domains.team.models import BaseTeam
from web.domains.user.models import User
from web.models.mixins import Archivable
from web.domains.office.models import Office


class Importer(Archivable, BaseTeam):
    # Regions
    INDIVIDUAL = "INDIVIDUAL"
    ORGANISATION = "ORGANISATION"
    TYPES = ((INDIVIDUAL, "Individual"), (ORGANISATION, "Organisation"))

    # Region Origins
    UK = None
    EUROPE = "E"
    NON_EUROPEAN = "O"
    REGIONS = ((UK, "UK"), (EUROPE, 'Europe'), (NON_EUROPEAN, 'Non-European'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    type = models.CharField(max_length=20,
                            choices=TYPES,
                            blank=False,
                            null=False)
    # Organisation's name
    name = models.CharField(max_length=4000, blank=True, null=True)
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    eori_number = models.CharField(max_length=20, blank=True, null=True)
    region_origin = models.CharField(max_length=1,
                                     choices=REGIONS,
                                     blank=True,
                                     null=True)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    offices = models.ManyToManyField(Office)
    # Having a main importer means importer is an agent
    main_importer = models.ForeignKey("self",
                                      on_delete=models.SET_NULL,
                                      blank=True,
                                      null=True,
                                      related_name='agents')
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True,
                             related_name='own_importers')

    def is_agent(self):
        return self.main_importer is not None

    @property
    def entity_type(self):
        return dict(Importer.TYPES)[self.type]

    class Display:
        display = [('full_name', 'registered_number', 'entity_type')]
        labels = ['Importer Name / Importer Reg No / Importer Entity Type']
        edit = True
        view = True
        archive = True
