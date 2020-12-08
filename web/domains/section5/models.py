from django.db import models

from web.domains.user.models import User
from web.models.mixins import Archivable


class Section5Clause(Archivable, models.Model):
    clause = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+", blank=True, null=True
    )

    class Meta:
        ordering = ("clause",)
