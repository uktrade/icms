from types import DynamicClassAttribute

from django.db import models


class PermissionTextChoice(models.TextChoices):
    @DynamicClassAttribute
    def value(self) -> str:
        """Dynamically add the web app label to the permission name.

        All permissions are defined in the "web" app.
        e.g. "can_access_foo" becomes "web.can_access_foo"
        """

        # Note: if this causes issues in future then all permissions will need
        # prefixing with "web." to work throughout the system
        return f"web.{self._value_}"

    @classmethod
    def get_permissions(cls):
        """Return all the class permissions with the "web." prefix removed.

        This is required when setting permissions in a model class.
        e.g.
        class Meta:
            permissions = Perms.obj.exporter.get_permissions()
        """

        return [cls._remove_prefix(v) for v in cls.choices]

    @staticmethod
    def _remove_prefix(v: tuple[str, str]) -> tuple[str, str]:
        value, label = v

        return value.removeprefix("web."), label


class _PagePermissions(PermissionTextChoice):
    view_permission_harness = "can_view_permission_harness", "Can view the permission test harness"
    view_importer_details = "can_view_importer_details", "Can view the importer details list view."


class _SysPerms(PermissionTextChoice):
    importer_access = "importer_access", "Can act as an importer"
    exporter_access = "exporter_access", "Can act as an exporter"
    ilb_admin = "ilb_admin", "Is an ILB administrator"
    # This permission isn't used anywhere.
    mailshot_access = "mailshot_access", "Can maintain mailshots"


class _ImporterPermissions(PermissionTextChoice):
    is_contact = ("is_contact_of_importer", "Is contact of this importer")
    # NOTE: this is given on the "main importer" object, not on the "agent" object
    is_agent = ("is_agent_of_importer", "Is agent of this importer")


class _ExporterPermissions(PermissionTextChoice):
    is_contact = ("is_contact_of_exporter", "Is contact of this exporter")
    # NOTE: this is given on the "main exporter" object, not on the "agent" object
    is_agent = ("is_agent_of_exporter", "Is agent of this exporter")


class _ObjPerms:
    importer = _ImporterPermissions
    exporter = _ExporterPermissions


class Perms:
    page = _PagePermissions
    sys = _SysPerms
    obj = _ObjPerms

    @classmethod
    def get_all_permissions(cls) -> list[tuple[str, str]]:
        """Return all system-wide permissions defined in IMCS - Called when creating migrations."""

        return cls.page.get_permissions() + cls.sys.get_permissions()


class GlobalPermission(models.Model):
    """Contains global permissions.

    None of these should ever be assigned to users directly; all permissions
    should be granted to users by assigning the users to one or more groups.

    See
    https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model.
    """

    class Meta:
        managed = False
        default_permissions = []

        permissions = Perms.get_all_permissions()
