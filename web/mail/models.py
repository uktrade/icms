from django.db import models

from .constants import EmailTypes


class EmailTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True, choices=EmailTypes.choices)
    gov_notify_template_id = models.UUIDField()

    def __str__(self) -> str:
        return self.get_name_display()
