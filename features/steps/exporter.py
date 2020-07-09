from behave import given
from web.domains.exporter.models import Exporter
from web.domains.user.models import User
from web.tests.domains.exporter.factory import ExporterFactory


@given('exporter "{name}" exists')
def create_exporter(context, name):
    ExporterFactory(name=name, is_active=True)


@given('"{username}" is a member of exporter "{name}"')
def add_exporter_member(context, username, name):
    exporter = Exporter.objects.get(name=name)
    user = User.objects.get(username=username)
    exporter.members.add(user)


@given('"{agent_name}" is an agent of exporter "{name}"')
def mark_as_exporter_agent(context, agent_name, name):
    agent = Exporter.objects.get(name=agent_name)
    exporter = Exporter.objects.get(name=name)

    agent.main_exporter = exporter
    agent.save()
