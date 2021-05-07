from django.db import models

from web.models import ImportApplication


class DFLApplication(ImportApplication):
    """Firearms & Ammunition Deactivated Firearms Licence application"""

    PROCESS_TYPE = "DFLApplication"

    know_bought_from = models.BooleanField(
        null=True, verbose_name="Do you know who you plan to buy/obtain these items from?"
    )

    def __str__(self):
        return f"DFLApplication(id={self.pk}, status={self.status!r}, is_active={self.is_active})"
