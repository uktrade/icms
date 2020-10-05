import logging

import humanize
from django.conf import settings
from django.db import models

from web.domains.user.models import User
from web.models.mixins import Archivable
from web.utils import url_path_join

logger = logging.getLogger(__name__)


class ActiveManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class File(Archivable, models.Model):
    objects = ActiveManager()

    is_active = models.BooleanField(blank=False, null=False, default=True)
    filename = models.CharField(max_length=300, blank=False, null=True)
    content_type = models.CharField(max_length=100, blank=False, null=True)
    browser_content_type = models.CharField(max_length=100, blank=False, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    file_size = models.IntegerField(blank=False, null=True)
    path = models.CharField(max_length=4000, blank=True, null=True)
    error_message = models.CharField(max_length=4000, blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, blank=False, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, blank=False, null=True)

    class Meta:
        ordering = ["-created_datetime"]

    def date_created_formatted(self):
        """
            returns a formatted datetime
        """
        return self.created_datetime.strftime("%d-%b-%Y %H:%M:%S")

    def full_path(self):
        return url_path_join(settings.AWS_BASE_URL, settings.AWS_STORAGE_BUCKET_NAME, self.path)

    def human_readable_file_size(self):
        return humanize.naturalsize(self.file_size or 0)
