import logging

import humanize
from django.db import models

from web.domains.user.models import User
from web.models.mixins import Archivable

logger = logging.getLogger(__name__)


class ActiveManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class File(Archivable, models.Model):
    objects = ActiveManager()

    is_active = models.BooleanField(default=True)
    filename = models.CharField(max_length=300)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    path = models.CharField(max_length=4000)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_datetime"]

    def date_created_formatted(self):
        """
        returns a formatted datetime
        """
        return self.created_datetime.strftime("%d-%b-%Y %H:%M:%S")

    def human_readable_file_size(self):
        return humanize.naturalsize(self.file_size or 0)
