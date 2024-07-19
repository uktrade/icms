import logging

import humanize
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class ActiveManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class File(models.Model):
    objects = ActiveManager()

    is_active = models.BooleanField(default=True)
    filename = models.CharField(max_length=300)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    path = models.CharField(max_length=4000)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_datetime"]

    def date_created_formatted(self):
        """
        returns a formatted datetime
        """
        return self.created_datetime.strftime("%d-%b-%Y %H:%M:%S")

    def human_readable_file_size(self):
        return humanize.naturalsize(self.file_size or 0)

    def __str__(self):
        props = ("pk", "is_active", "filename", "content_type", "file_size", "path")
        attribute_values = ", ".join(f"{p}={getattr(self, p)!r}" for p in props)

        return f"File({attribute_values})"
