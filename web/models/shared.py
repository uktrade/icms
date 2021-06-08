from django.db import models


class YesNoChoices(models.TextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")


class YesNoNAChoices(models.TextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")
    not_applicable = ("n/a", "N/A")
