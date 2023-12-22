from django.db import models

from web.domains.file.models import File


class Signature(File):
    name = models.CharField(max_length=40)
    signatory = models.CharField(max_length=40)
    history = models.TextField(null=True)
