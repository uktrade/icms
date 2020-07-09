#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from web.domains.team.models import Role, Team
from web.domains.user.models import User
from web.tests.domains.user.factory import UserFactory


def login(context, username, password):
    """
        Type in username and password  and click on Sign in
    """
    username_field = context.browser.find_element(By.ID, "id_username")
    password_field = context.browser.find_element(By.ID, "id_password")
    submit_button = context.browser.find_element(By.XPATH, '//button[contains(text(),"Sign in")]')
    username_field.send_keys(username)
    password_field.send_keys(password)
    submit_button.click()


def go_to_page(context, url_name, **kwargs):
    """
        Navigate to page with given url name
    """
    url = context.get_url(url_name, **kwargs)
    context.browser.get(url)


def assert_on_page(context, expected_url_name, **kwargs):
    """
        Assert current url is the expected url
    """
    page_url = context.browser.current_url.split("?")[0]
    expected_url = context.get_url(expected_url_name, **kwargs)
    assert expected_url == page_url, f"expecting url to be {expected_url} but got {page_url}"


def assert_context_header(context, expected_header):
    """
        Assert ICMS internal page context header is given text
    """
    header = context.browser.find_element_by_css_selector("#context-header h2")
    assert (
        header.text == expected_header
    ), f'expecting header with text "{expected_header}" but got {header.text}'


def create_active_user(username, title=None, first_name=None, last_name=None):
    args = {
        "username": username,
        "is_active": True,
        "is_superuser": False,
        "account_status": User.ACTIVE,
        "password_disposition": User.FULL,
    }

    if title is not None:
        args["title"] = title

    if first_name is not None:
        args["first_name"] = first_name

    if last_name is not None:
        args["last_name"] = last_name

    return UserFactory(**args)


def find_element_by_text(context, text, element_type="*"):
    try:
        return context.browser.find_element(
            By.XPATH, f'//{element_type}[contains(text(),"{text}")]'
        )
    except Exception as e:
        print(e)
        return None


def to_boolean(str):
    return str.lower() in ["true", "1", "t", "y", "yes"]


def add_user_to_team(username, team_name):
    """
        Add user with given username to the team with given team_name
    """
    team = Team.objects.get(name=team_name)
    user = User.objects.get(username=username)
    team.members.add(user)


def give_role(username, role_name):
    """
        Give user with given username the role with fiven role_name
    """
    role = Role.objects.get(name=role_name)
    user = User.objects.get(username=username)
    role.user_set.add(user)
