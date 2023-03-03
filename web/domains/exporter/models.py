from django.db import models

from web.domains.office.models import Office
from web.models.mixins import Archivable
from web.permissions import Perms


class ExporterManager(models.Manager):
    def agents(self):
        return self.filter(main_exporter__isnull=False)


# TODO: explore if we should use the "direct foreign keys" for django-guardian
# for efficiency; see https://django-guardian.readthedocs.io/en/stable/userguide/performance.html
class Exporter(Archivable, models.Model):
    objects = ExporterManager()

    is_active = models.BooleanField(blank=False, null=False, default=True)
    name = models.TextField(verbose_name="Organisation Name")
    registered_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Registered Number"
    )
    comments = models.TextField(blank=True, null=True)
    offices = models.ManyToManyField(Office)

    # Having a main exporter means exporter is an agent
    main_exporter = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="agents"
    )

    def is_agent(self):
        return self.main_exporter is not None

    def __str__(self):
        if self.is_agent():
            return f"Agent - {self.name}"

        return self.name

    class Meta:
        ordering = (
            "-is_active",
            "name",
        )

        permissions = Perms.obj.exporter.get_permissions()
