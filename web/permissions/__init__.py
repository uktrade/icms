from .models import Perms

importer_object_permissions = Perms.obj.importer.get_permissions()
exporter_object_permissions = Perms.obj.exporter.get_permissions()


__all__ = [
    "Perms",
    "importer_object_permissions",
    "exporter_object_permissions",
]
