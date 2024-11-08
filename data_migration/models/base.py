from django.db import models


class MigrationBase(models.Model):
    class Meta:
        abstract = True
