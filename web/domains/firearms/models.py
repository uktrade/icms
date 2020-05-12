from django.db import models
from web.domains.constabulary.models import Constabulary
from web.domains.file.models import File
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.models.mixins import Archivable, Sortable


class FirearmsAuthority(models.Model):
    DEACTIVATED_FIREARMS = 'DEACTIVATED'
    FIREARMS = 'FIREARMS'
    REGISTERED_FIREARMS_DEALER = 'RFD'
    SHOTGUN = 'SHOTGUN'

    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, 'Manual'), (SEARCH, 'Search'))

    CERTIFICATE_TYPES = ((DEACTIVATED_FIREARMS, 'Deactivation Certificate'),
                         (FIREARMS, 'Firearms Certificate'),
                         (REGISTERED_FIREARMS_DEALER,
                          'Registered Firearms Dealer Certificate'),
                         (SHOTGUN, 'Shotgun Certificate'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    reference = models.CharField(max_length=50, blank=False, null=True)
    certificate_type = models.CharField(max_length=20,
                                        choices=CERTIFICATE_TYPES,
                                        blank=False,
                                        null=True)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=300, blank=False, null=True)
    address_entry_type = models.CharField(max_length=10,
                                          blank=False,
                                          null=True)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)
    further_details = models.CharField(max_length=4000, blank=True, null=True)
    issuing_constabulary = models.ForeignKey(Constabulary,
                                             on_delete=models.PROTECT,
                                             blank=False,
                                             null=True)
    linked_offices = models.ManyToManyField(Office)
    importer = models.ForeignKey(Importer,
                                 on_delete=models.PROTECT,
                                 blank=False,
                                 null=False,
                                 related_name='firearms_authorities')
    files = models.ManyToManyField(File)


class ObsoleteCalibreGroup(Archivable, Sortable, models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False)

    def __str__(self):
        if self.id:
            return f'Obsolete Calibre Group ({self.name})'
        else:
            return f'Obsolete Calibre Group (new) '

    class Meta:
        ordering = ('order', '-is_active')


class ObsoleteCalibre(Archivable, models.Model):
    calibre_group = models.ForeignKey(ObsoleteCalibreGroup,
                                      on_delete=models.CASCADE,
                                      blank=False,
                                      null=False,
                                      related_name='calibres')
    name = models.CharField(max_length=200, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False)

    def __str__(self):
        if self.id:
            return f'Obsolete Calibre ({self.name})'
        else:
            return f'Obsolete Calibre (New) '

    @property
    def status(self):
        if not self.id:
            return 'Pending'
        elif not self.is_active:
            return 'Archived'
        else:
            return 'Current'

    class Meta:
        ordering = ('order', )


class Section5Authority(models.Model):
    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, 'Manual'), (SEARCH, 'Search'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    reference = models.CharField(max_length=50, blank=False, null=True)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=300, blank=False, null=True)
    address_entry_type = models.CharField(max_length=10,
                                          blank=False,
                                          null=True)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)
    further_details = models.CharField(max_length=4000, blank=True, null=True)
    linked_offices = models.ManyToManyField(Office)
    importer = models.ForeignKey(Importer,
                                 on_delete=models.PROTECT,
                                 blank=False,
                                 null=False,
                                 related_name='section5_authorities')
    files = models.ManyToManyField(File)
