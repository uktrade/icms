from django.db import models
from web.domains.team.models import BaseTeam
from web.models.mixins import Archivable


class UserAccount(Archivable, BaseTeam):
    EAST_MIDLANDS = 'EM'
    EASTERN = 'ER'
    ISLE_OF_MAN = 'IM'
    LONDON = 'LO'
    NORTH_EAST = 'NE'
    NORTH_WEST = 'NW'
    ROYAL_ULSTER = 'RU'
    SCOTLAND = 'SC'
    SOUTH_EAST = 'SE'
    SOUTH_WEST = 'SW'
    WEST_MIDLANDS = 'WM'

    REGIONS = ((EAST_MIDLANDS, 'East Midlands'), (EASTERN, 'Eastern'),
               (ISLE_OF_MAN, 'Isle of Man'), (
                   LONDON,
                   'London',
               ), (NORTH_EAST, 'North East'), (NORTH_WEST, 'North WEST'),
               (ROYAL_ULSTER, 'Royal Ulster'), (SCOTLAND, 'Scotland'),
               (SOUTH_EAST, 'South East'), (SOUTH_WEST, 'South West'),
               (WEST_MIDLANDS, 'West Midlands'))

    name = models.CharField(max_length=50, blank=False, null=False)
    region = models.CharField(max_length=3,
                              choices=REGIONS,
                              blank=False,
                              null=False)
    email = models.EmailField(max_length=254, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    @property
    def region_verbose(self):
        return dict(UserAccount.REGIONS)[self.region]
