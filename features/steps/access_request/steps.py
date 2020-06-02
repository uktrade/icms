from behave import then, when, given
from features.steps.shared import find_element_with_text, to_boolean, user_logs_in, user_navigates_to_page
from selenium.webdriver.common.by import By


@then(u'Request Importer/Exporter Access page is displayed')
def step_impl(context):
    assert find_element_with_text(context, 'Request Importer/Exporter Access', 'h2'), 'Page title not found'


@when(u'user sets Access Request Type to "{text}"')
def se(context, text):
    context.browser.find_element_by_xpath(f"//select[@name='request_type']/option[text()='{text}']").click()


@then(u'the following fields visibility is set on the act as an importer/exporter form')
def step_impl(context):
    for text,is_visible in context.table:
        label = find_element_with_text(context, text, 'label')
        assert label, f"label with text {text} not found"

        assert label.is_displayed() ==  to_boolean(is_visible), f"expeting {text} visibility to be {is_visible} but it is {label.is_displayed()}"


@given(u'user requests to act as an importer')
@when(u'user requests to act as an importer')
def step_impl(context):
    text = 'Request access to act as an Importer'
    context.browser.find_element_by_xpath(f"//select[@name='request_type']/option[text()='{text}']").click()

    context.browser.find_element_by_id('id_organisation_name').send_keys('functional test ltd')
    context.browser.find_element_by_id('id_organisation_address').send_keys("1 BDD street\n BBD-000\nLondon")
    context.browser.find_element_by_id('id_request_reason').send_keys("better tests")

    context.browser.find_element_by_css_selector('button[type=submit]').click()


@given(u'user requests to act as an agent for an importer')
@when(u'user requests to act as an agent for an importer')
def step_impl(context):
    text = 'Request access to act as an Agent for an Importer'
    context.browser.find_element_by_xpath(f"//select[@name='request_type']/option[text()='{text}']").click()

    context.browser.find_element_by_id('id_organisation_name').send_keys('functional test ltd')
    context.browser.find_element_by_id('id_organisation_address').send_keys("1 BDD street\n BBD-000\nLondon")
    context.browser.find_element_by_id('id_request_reason').send_keys("better tests")
    context.browser.find_element_by_id('id_agent_name').send_keys("BDD Agent")
    context.browser.find_element_by_id('id_agent_address').send_keys("1 BDD Agent street\n BBD-000\nLondon")

    context.browser.find_element_by_css_selector('button[type=submit]').click()


@given(u'user requests to act as an agent for an exporter')
@when(u'user requests to act as an agent for an exporter')
def step_impl(context):
    text = 'Request access to act as an Agent for an Exporter'
    context.browser.find_element_by_xpath(f"//select[@name='request_type']/option[text()='{text}']").click()

    context.browser.find_element_by_id('id_organisation_name').send_keys('functional test ltd')
    context.browser.find_element_by_id('id_organisation_address').send_keys("1 BDD street\n BBD-000\nLondon")
    context.browser.find_element_by_id('id_agent_name').send_keys("BDD Agent")
    context.browser.find_element_by_id('id_agent_address').send_keys("1 BDD Agent street\n BBD-000\nLondon")

    context.browser.find_element_by_css_selector('button[type=submit]').click()


@when(u'user requests to act as an exporter')
@given(u'user requests to act as an exporter')
def step_impl(context):
    text = 'Request access to act as an Exporter'
    context.browser.find_element_by_xpath(f"//select[@name='request_type']/option[text()='{text}']").click()

    context.browser.find_element_by_id('id_organisation_name').send_keys('functional test ltd')
    context.browser.find_element_by_id('id_organisation_address').send_keys("1 BDD street\n BBD-000\nLondon")

    context.browser.find_element_by_css_selector('button[type=submit]').click()

@then(u'a success message is displayed')
def step_impl(context):
     assert find_element_with_text(context, 'Your access request has been submitted to ILB', '*/div[contains(@class, "info-box-success") ]/p'), 'Success message not found'


@given(u'there are {count} Pending Access Requests to act as an importer')
@then(u'there are {count} Pending Access Requests to act as an importer')
def step_impl(context, count):
    elements = context.browser.find_elements_by_css_selector('.pending-import-requests .main-entry')
    element_count = len(elements)

    assert element_count == int(count), f'expecting {count} of elements in pending import requests but found {element_count}'


@given(u'there are {count} Pending Access Requests to act as an exporter')
@then(u'there are {count} Pending Access Requests to act as an exporter')
def step_impl(context, count):
    elements = context.browser.find_elements_by_css_selector('.pending-export-requests .main-entry')
    element_count = len(elements)

    assert element_count == int(count), f'expecting {count} of elements in pending export requests but found {element_count}'
