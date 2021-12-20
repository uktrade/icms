#!/usr/bin/env python
# -*- coding: utf-8 -*-

from behave import given, then, when
from django.contrib.auth.models import Permission

from features.steps import utils
from web.domains.user.models import User


@given('user "{username}" exists')
def create_user(context, username):
    utils.create_active_user(username)


@given('"{username}" has permission "{codename}"')
def grant_permission_to_user(context, username, codename):
    permission = Permission.objects.get(codename=codename)
    user = User.objects.get(username=username)
    user.user_permissions.add(permission)


@given(
    'user "{username}" exists with title "{title}" and first name "{first_name}" and last name "{last_name}"'  # /PS-IGNORE
)
def create_user_named(context, username, title, first_name, last_name):
    utils.create_active_user(
        username=username, title=title, first_name=first_name, last_name=last_name
    )


@when('navigates to "{url_name}"')
@when('the user navigates to "{url_name}"')
@when('an anonymous user navigates to "{url_name}"')
def navigate(context, url_name):
    utils.go_to_page(context, url_name)


@when('"{username}" navigates to "{url_name}"')
def user_navigates(context, username, url_name):
    utils.go_to_page(context, url_name)


@when('clicks on link "{text}"')
def clicks_on_link(context, text):
    utils.find_element_by_text(context, text, "a").click()


@when('clicks on button "{text}"')
def clicks_on_button(context, text):
    utils.find_element_by_text(context, text, "button").click()


@then('button "{text}" is visible')
def button_visible(context, text):
    assert utils.find_element_by_text(context, text, "button"), f"button {text} not found!"


@then('section title "{text}" is visible')
def section_title_visible(context, text):
    assert utils.find_element_by_text(context, text, "h3"), f"section title {text} not found!"


@then('link "{text}" is visible')
def link_visible(context, text):
    assert utils.find_element_by_text(context, text, "a"), f"link {text} not found!"


@then('"{url_name}" page is displayed')
def page_displayed(context, url_name):
    utils.assert_on_page(context, url_name)


@then("the user is logged out")
def user_is_logged_out(context):
    # try to navigate to workbasket
    # ensure the login page is displayed
    utils.go_to_page(context, "workbasket")
    utils.assert_on_page(context, "login")


@given('"{username}" is logged in')
@when('"{username}" logs in')
def login(context, username):
    utils.create_active_user(username)
    utils.go_to_page(context, "login")
    utils.login(context, username, "test")


@then('context header reads "{expected_header}"')
def context_header_is(context, expected_header):
    utils.assert_context_header(context, expected_header)


@then('text "{text}" is visible')
def text_is_visible(context, text):
    assert utils.find_element_by_text(context, text), f"could not find text {text} in page"


@then("403 error page is displayed")
def check_unauhorised_page(context):
    text_is_visible(context, "403 Forbidden")
