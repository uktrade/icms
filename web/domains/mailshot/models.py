from django.db import models
from web.domains.file.models import File
from web.domains.user.models import User


class Mailshot(models.Model):
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    RETRACTED = 'RETRACTED'
    CANCELLED = 'CANCELLED'

    STATUSES = ((DRAFT, 'Draft'), (PUBLISHED, 'Published'),
                (RETRACTED, 'Retracted'), (CANCELLED, 'Cancelled'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=20, blank=False, null=False)
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=4000, blank=True, null=True)
    is_email = models.BooleanField(blank=False, null=False, default=True)
    email_subject = models.CharField(max_length=78, blank=False, null=True)
    email_body = models.CharField(max_length=4000, blank=False, null=True)
    is_retraction_email = models.BooleanField(blank=False, null=False)
    retract_email_subject = models.CharField(max_length=78,
                                             blank=False,
                                             null=True)
    retract_email_body = models.CharField(max_length=4000,
                                          blank=False,
                                          null=True)
    is_to_importers = models.BooleanField(blank=False,
                                          null=False,
                                          default=False)
    is_to_exporters = models.BooleanField(blank=False,
                                          null=False,
                                          default=False)
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   blank=False,
                                   null=False,
                                   related_name='created_mailshots')
    create_datetime = models.DateTimeField(blank=False,
                                           null=False,
                                           auto_now_add=True)
    published_by = models.ForeignKey(User,
                                     on_delete=models.PROTECT,
                                     blank=False,
                                     null=True,
                                     related_name='published_mailshots')
    published_datetime = models.DateTimeField(blank=False, null=True)
    retracted_by = models.ForeignKey(User,
                                     on_delete=models.PROTECT,
                                     blank=False,
                                     null=True,
                                     related_name='retracted_mailshots')
    retracted_datetime = models.DateTimeField(blank=False, null=True)
    files = models.ManyToManyField(File)

    @property
    def started(self):
        if self.create_datetime:
            return self.create_datetime.strftime('%d %b %Y %H:%M')

    @property
    def published(self):
        if self.published_datetime:
            return self.published_datetime.strftime('%d %b %Y %H:%M')

    @property
    def retracted(self):
        if self.retracted_datetime:
            return self.retracted_datetime.strftime('%d %b %Y %H:%M')

    @property
    def status_verbose(self):
        return dict(Mailshot.STATUSES)[self.status]

    class Meta:
        ordering = ('-id', )
