from django.core.validators import MinValueValidator
from django.db import models


class YesNoChoices(models.TextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")


class YesNoNAChoices(models.TextChoices):
    yes = ("yes", "Yes")
    no = ("no", "No")
    not_applicable = ("n/a", "N/A")


class FirearmCommodity(models.TextChoices):
    EX_CHAPTER_93 = ("ex Chapter 93", "ex Chapter 93")
    EX_CHAPTER_97 = ("ex Chapter 97", "ex Chapter 97")


at_least_0 = MinValueValidator(limit_value=0.0)
