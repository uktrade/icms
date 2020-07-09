#!/usr/bin/env python
# -*- coding: utf-8 -*-

from behave import given
from behave_django.decorators import fixtures
from features.steps import utils


@fixtures("team.yaml")
@given('"{username}" is a member of "{team_name}"')
def add_user_to_team(context, username, team_name):
    utils.add_user_to_team(username, team_name)


@fixtures("role.yaml")
@given('"{username}" has "{role_name}" role')
def team_member_login(context, username, role_name):
    utils.give_role(username, role_name)
