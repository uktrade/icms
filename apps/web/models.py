from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    title = models.CharField(max_length=20, blank=False, null=True)
    phone = models.CharField(max_length=60, blank=False, null=True)
    organisation = models.CharField(max_length=4000, blank=False, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    security_question = models.CharField(
        max_length=4000, blank=False, null=True)
    security_answer = models.CharField(max_length=4000, blank=False, null=True)
