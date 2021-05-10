from django.db import models

from web.models import ImportApplication


class DFLApplication(ImportApplication):
    """Firearms & Ammunition Deactivated Firearms Licence application"""

    PROCESS_TYPE = "DFLApplication"

    deactivated_firearm = models.BooleanField(verbose_name="Deactivated Firearm", default=True)
    proof_checked = models.BooleanField(verbose_name="Proof Checked", default=False)

    know_bought_from = models.BooleanField(
        null=True, verbose_name="Do you know who you plan to buy/obtain these items from?"
    )

    def __str__(self):
        return f"DFLApplication(id={self.pk}, status={self.status!r}, is_active={self.is_active})"
