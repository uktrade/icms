from behave import then, when
from features.steps import utils


def fill_organisation_name(context, name):
    context.browser.find_element_by_id('id_organisation_name').send_keys(name)


def fill_agent_name(context, name):
    context.browser.find_element_by_id('id_agent_name').send_keys(name)


def fill_agent_address(context, address):
    context.browser.find_element_by_id('id_agent_address').send_keys(address)


def fill_organisation_address(context, address):
    context.browser.find_element_by_id('id_organisation_address').send_keys(
        address)


def fill_request_reason(context, reason):
    context.browser.find_element_by_id('id_request_reason').send_keys(reason)


def submit_access_request_form(context):
    context.browser.find_element_by_css_selector('button[type=submit]').click()


@when(u'sets Access Request Type to "{text}"')
def set_access_request_type(context, text):
    context.browser.find_element_by_xpath(
        f"//select[@name='request_type']/option[text()='{text}']").click()


@then(u'following fields are visible on access request form')
def fields_visible(context):
    for text, is_visible in context.table:
        label = utils.find_element_by_text(context, text, 'label')
        assert label, f"label with text {text} not found"

        assert label.is_displayed() == utils.to_boolean(
            is_visible
        ), f"expeting {text} visibility to be {is_visible} but it is {label.is_displayed()}"


@when(u'the user requests to act as an importer')
def request_importer_access(context):
    utils.go_to_page(context, 'access:request')
    option = 'Request access to act as an Importer'
    set_access_request_type(context, option)

    fill_organisation_name(context, 'some importer')
    fill_organisation_address(context, "1 BDD street\n BBD-000\nLondon")
    fill_request_reason(context, 'just testing')
    submit_access_request_form(context)


@when(u'the user requests to act as an exporter')
def request_exporter_access(context):
    utils.go_to_page(context, 'access:request')
    option = 'Request access to act as an Exporter'
    set_access_request_type(context, option)

    fill_organisation_name(context, 'some exporter')
    fill_organisation_address(context, "1 BDD street\n BBD-000\nLondon")
    submit_access_request_form(context)


@when(u'the user requests to act as an agent of an importer')
def request_importer_agent_access(context):
    utils.go_to_page(context, 'access:request')
    option = 'Request access to act as an Agent for an Importer'
    set_access_request_type(context, option)

    fill_organisation_name(context, 'best imports ltd')
    fill_organisation_address(context, "Somewhere")
    fill_request_reason(context, 'testing the agent')
    fill_agent_name(context, 'best agent for importers ltd.')
    fill_agent_address(context, 'next to the buthcer')
    submit_access_request_form(context)


@when(u'the user requests to act as an agent of an exporter')
def request_exporter_agent_access(context):
    utils.go_to_page(context, 'access:request')
    option = 'Request access to act as an Agent for an Exporter'
    set_access_request_type(context, option)

    fill_organisation_name(context, 'dude exporters ltd')
    fill_organisation_address(context, "London")
    fill_agent_name(context, 'dude export agents ltd.')
    fill_agent_address(context, 'Manchester')
    submit_access_request_form(context)


@then(u'a success message is displayed')
def success_message_displayed(context):
    assert utils.find_element_by_text(
        context, 'Your access request has been submitted to ILB',
        '*/div[contains(@class, "info-box-success") ]/p'
    ), 'Success message not found'


@then(u'there are {count} pending access requests to act as an importer')
def check_pending_importer_requests(context, count):
    elements = context.browser.find_elements_by_css_selector(
        '.pending-import-requests .main-entry')
    element_count = len(elements)

    assert element_count == int(
        count
    ), f'expecting {count} of elements in pending import requests but found {element_count}'


@then(u'there are {count} pending access requests to act as an exporter')
def check_pending_exporter_requests(context, count):
    elements = context.browser.find_elements_by_css_selector(
        '.pending-export-requests .main-entry')
    element_count = len(elements)

    assert element_count == int(
        count
    ), f'expecting {count} of elements in pending export requests but found {element_count}'
