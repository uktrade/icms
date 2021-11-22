import typing

from django.db import models

if typing.TYPE_CHECKING:
    from .models import CertificateApplicationTemplate


class CATManager(models.Manager):
    def active(self) -> "models.QuerySet[CertificateApplicationTemplate]":
        return self.filter(is_active=True)

    def inactive(self) -> "models.QuerySet[CertificateApplicationTemplate]":
        return self.filter(is_active=False)
