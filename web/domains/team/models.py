from django.contrib.auth.models import Group, Permission
from django.db import models, transaction

from web.domains.user.models import User


def _create_team_roles(team):
    """
        Creates given roles and permissions for given team
    """
    if not team.role_list:
        return

    for r in team.role_list:
        role = Role.objects.create(name=r['name'].format(id=team.id),
                                   description=r['description'],
                                   role_order=r['role_order'])

        permissions = Permission.objects.filter(codename__in=r['permissions'])
        role.permissions.add(*permissions)


class BaseTeam(models.Model):
    members = models.ManyToManyField(User)
    role_list = None  # List of roles with permissions to create for the team with each instance

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
            Create roles/permissions for new team instance if provided
            See importers/exporters/constabularies for list of roles
        """
        _id = self.pk
        result = super().save(*args, **kwargs)
        if not _id:  # new object
            if self.role_list:
                _create_team_roles(self)
        return result


class Team(BaseTeam):
    name = models.CharField(max_length=1000, blank=False, null=False)
    description = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        ordering = ('name', )


class Role(Group):
    group = models.OneToOneField(Group,
                                 on_delete=models.CASCADE,
                                 parent_link=True,
                                 related_name='roles')
    description = models.CharField(max_length=4000, blank=True, null=True)
    # Display order on the screen
    role_order = models.IntegerField(blank=False, null=False)
    team = models.ForeignKey(BaseTeam, on_delete=models.CASCADE)

    def has_member(self, user):
        return user in self.user_set.all()

    @property
    def short_name(self):
        return self.name.split(':')[1]

    class Meta:
        ordering = ('role_order', )
