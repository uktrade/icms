from django.db import models


class GlobalPermission(models.Model):
    """Contains global permissions that are not tied to a specific model.

    None of these should ever be assigned to users directly; all permissions
    should be granted to users by assigning the users to one or more groups.

    See
    https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model.
    """

    class Meta:
        managed = False
        default_permissions = []

        permissions = (
            ("importer_access", "Can act as an importer"),
            ("exporter_access", "Can act as an exporter"),
            ("ilb_admin", "Is an ILB administrator"),
            ("mailshot_access", "Can maintain mailshots"),
        )
