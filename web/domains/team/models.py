from django.contrib.auth.models import Group
from django.db import models
from web.domains.user.models import User


class Role(Group):
    group = models.OneToOneField(Group,
                                 on_delete=models.CASCADE,
                                 parent_link=True,
                                 related_name='roles')
    description = models.CharField(max_length=4000, blank=True, null=True)
    # Display order on the screen
    role_order = models.IntegerField(blank=False, null=False)

    def has_member(self, user):
        return user in self.user_set.all()

    @property
    def short_name(self):
        return self.name.split(':')[1]

    class Meta:
        ordering = ('role_order', )


class BaseTeam(models.Model):
    roles = models.ManyToManyField(Role)
    members = models.ManyToManyField(User)

    class Meta:
        abstract = True


class Team(BaseTeam):
    name = models.CharField(max_length=1000, blank=False, null=False)
    description = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        ordering = ('name', )

    class Display:
        display = ['name']
        labels = ['Name']
        edit = True
