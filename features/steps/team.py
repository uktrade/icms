from behave import given
from behave_django.decorators import fixtures
from web.domains.team.models import Role, Team
from web.domains.user.models import User


@fixtures("team.yaml")
@given('"{username}" is a member of "{team_name}"')
def add_user_to_team(context, username, team_name):
    team = Team.objects.get(name=team_name)
    user = User.objects.get(username=username)
    team.members.add(user)


@fixtures("role.yaml")
@given('"{username}" has "{role_name}" role')
def assign_role(context, username, role_name):
    role = Role.objects.get(name=role_name)
    user = User.objects.get(username=username)
    role.user_set.add(user)
