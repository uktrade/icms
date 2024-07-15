import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase


class ExporterObjectPerms:
    """Return object permissions linked to the exporter model.

    Implemented this way to resolve a circular import dependency.
    The permissions module needs to be able to import models so this ensures it can.
    """

    def __init__(self):
        self._perms = []

    def __iter__(self):
        if not self._perms:
            self._load()

        return iter(self._perms)

    def __eq__(self, other):
        """This is required to prevent django creating a new migration each time for this model."""

        return list(self) == list(other)

    def _load(self):
        from web.permissions import exporter_object_permissions

        self._perms = exporter_object_permissions


class ExporterManager(models.Manager):
    def agents(self):
        return self.filter(main_exporter__isnull=False)


class Exporter(models.Model):
    objects = ExporterManager()

    is_active = models.BooleanField(blank=False, null=False, default=True)
    name = models.TextField(verbose_name="Organisation Name")
    registered_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Registered Number"
    )
    comments = models.TextField(blank=True, null=True)
    offices = models.ManyToManyField("web.Office")

    # Having a main exporter means exporter is an agent
    main_exporter = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="agents"
    )
    exclusive_correspondence = models.BooleanField(default=False)

    def get_edit_view_name(self) -> str:
        if self.is_agent():
            return reverse("exporter-agent-edit", kwargs={"pk": self.pk})

        return reverse("exporter-edit", kwargs={"pk": self.pk})

    def is_agent(self):
        return self.main_exporter is not None

    def get_main_org(self):
        return self.main_exporter

    def __str__(self):
        if self.is_agent():
            return f"Agent - {self.name}"

        return self.name

    class Meta:
        ordering = (
            "-is_active",
            "name",
        )

        default_permissions: list[str] = []
        permissions = ExporterObjectPerms()


class ExporterContactInvite(models.Model):
    organisation = models.ForeignKey("web.Exporter", on_delete=models.CASCADE)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    processed = models.BooleanField(default=False)
    code = models.UUIDField(default=uuid.uuid4, editable=False)


# Direct foreign key support for Django-Guardian
# https://django-guardian.readthedocs.io/en/stable/userguide/performance.html#direct-foreign-keys
class ExporterUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey("web.Exporter", on_delete=models.CASCADE)


class ExporterGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey("web.Exporter", on_delete=models.CASCADE)
