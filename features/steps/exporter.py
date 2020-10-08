from behave import given
from guardian.shortcuts import assign_perm

from web.domains.exporter.models import Exporter
from web.domains.user.models import User
from web.tests.domains.exporter.factory import ExporterFactory


@given('exporter "{name}" exists')
def create_exporter(context, name):
    ExporterFactory(name=name, is_active=True)


@given('"{username}" is a contact of exporter "{name}"')
def add_exporter_contact(context, username, name):
    exporter = Exporter.objects.get(name=name)
    user = User.objects.get(username=username)
    assign_perm("web.is_contact_of_exporter", user, exporter)


@given('"{agent_name}" is an agent of exporter "{name}"')
def mark_as_exporter_agent(context, agent_name, name):
    agent = Exporter.objects.get(name=agent_name)
    exporter = Exporter.objects.get(name=name)

    agent.main_exporter = exporter
    agent.save()
