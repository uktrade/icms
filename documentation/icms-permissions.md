# Permissions in ICMS.

## Overview

Permissions in ICMS use django's built in [permission framework](https://docs.djangoproject.com/en/4.2/topics/auth/default/#permissions-and-authorization).

Where object permission checking is needed [django-guardian](https://django-guardian.readthedocs.io/en/stable/index.html) has been used.

All permissions in ICMS are defined in a single file [perms.py](../web/permissions/perms.py) for simplicity.

The `Perms` class holds several types of permissions:
- sys: Permission for a particular feature.
- page: Permission restricting access to a certain view.
- obj: Permissions tied to specific models.

All system / page permissions are linked to the global permissions model `GlobalPermission` located [here](../web/models/models.py).

User object permissions are defined on models that require them: 
- [ImporterObjectPerms](../web/domains/importer/models.py) (see `permissions = ImporterObjectPerms()`)
- [ExporterObjectPerms](../web/domains/exporter/models.py) (see `permissions = ExporterObjectPerms()`)

**Users are never assigned system / page permissions directly they are always assigned to groups which have associated permissions.**

The available groups that can be assigned to users are located [here](../web/management/commands/create_icms_groups.py). 

## Authentication backend

A custom authentication backend has been created to combine django's ModelBackend and django-guardian's ObjectPermissionBackend.

The main differences are as follows:
- Only group permissions are checked when checking system / page permissions.
- `ObjectPermissionChecker` is cached after the first call to `user.has_perm()` or `user.get_all_permissions()` for object permission checking.

See [ModelAndObjectPermissionBackend](../web/auth/backends.py)

## Other Files of interest

- [Permissions module](../web/permissions/__init__.py) contains most of the permission checking code.
- [user_obj_perms](../web/permissions/context_processors.py): Global context variable to fetch user object permissions in templates for the request user.
- [get_user_obj_perms](../web/jinja2.py): Jinja function to load user object permissions for a given user.