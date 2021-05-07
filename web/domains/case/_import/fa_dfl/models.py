from web.models import ImportApplication


class DFLApplication(ImportApplication):
    """Firearms & Ammunition Deactivated Firearms Licence application"""

    PROCESS_TYPE = "DFLApplication"

    def __str__(self):
        return f"DFLApplication(id={self.pk}, status={self.status!r}, is_active={self.is_active})"
