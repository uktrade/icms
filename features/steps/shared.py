#!/usr/bin/env python
# -*- coding: utf-8 -*-

from behave import given, then, when
from features.steps import utils


@given('user "{username}" exists')
def create_user(context, username):
    utils.create_active_user(username)


@when('navigates to "{url_name}"')
@when('the user navigates to "{url_name}"')
@when('an anonymous user navigates to "{url_name}"')
def navigate(context, url_name):
    utils.go_to_page(context, url_name)


@when('"{username}" navigates to "{url_name}"')
def user_navigates(context, username, url_name):
    utils.go_to_page(context, url_name)


@then('"{url_name}" page is displayed')
def page_displayed(context, url_name):
    utils.assert_on_page(context, url_name)


@then(u'the user is logged out')
def user_is_logged_out(context):
    # try to navigate to workbasket
    # ensure the login page is displayed
    utils.go_to_page(context, 'workbasket')
    utils.assert_on_page(context, 'login')


@given('"{username}" is logged in')
@when('"{username}" logs in')
def login(context, username):
    utils.create_active_user(username)
    utils.go_to_page(context, 'login')
    utils.login(context, username, 'test')


@then('context header reads "{expected_header}"')
def context_header_is(context, expected_header):
    utils.assert_context_header(context, expected_header)


@then(u'text "{text}" is visible')
def text_is_visible(context, text):
    assert utils.find_element_by_text(
        context, text), f'could not find text {text} in page'


@then(u'403 error page is displayed')
def check_unauhorised_page(context):
    text_is_visible(context, '403 Forbidden')
