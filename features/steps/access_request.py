from behave import given, then, when

from features.steps import utils
from web.domains.case.access import flows
from web.domains.case.access.approval.flows import ApprovalRequestFlow
from web.domains.case.access.models import AccessRequest
from web.domains.importer.models import Importer
from web.domains.user.models import User
from web.tests.domains.case.access import factory
from web.tests.domains.case.access.approval.factory import (
    ApprovalRequestFactory,
    ApprovalRequestTaskFactory,
)


def fill_organisation_name(context, name):
    context.browser.find_element_by_id("id_organisation_name").send_keys(name)


def fill_agent_name(context, name):
    context.browser.find_element_by_id("id_agent_name").send_keys(name)


def fill_agent_address(context, address):
    context.browser.find_element_by_id("id_agent_address").send_keys(address)


def fill_organisation_address(context, address):
    context.browser.find_element_by_id("id_organisation_address").send_keys(address)


def fill_request_reason(context, reason):
    context.browser.find_element_by_id("id_request_reason").send_keys(reason)


def submit_access_request_form(context):
    context.browser.find_element_by_css_selector("button[type=submit]").click()


@given("an importer access request task exists")
def create_importer_access_request_task(context):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.IMPORTER)
    factory.ImporterAccessRequestTaskFactory(process__access_request=access_request)


@given("an exporter access request task exists")
def create_exporter_access_request(context):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.EXPORTER)
    factory.ExporterAccessRequestTaskFactory(process__access_request=access_request)


@given('an importer access request task owned by "{username}" exists')
def assign_importer_access_request_task(context, username):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.IMPORTER)
    factory.ImporterAccessRequestTaskFactory(
        owner=User.objects.get(username=username), process__access_request=access_request
    )


@given('an exporter access request task owned by "{username}" exists')
def assign_exporter_access_request_task(context, username):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.EXPORTER)
    factory.ExporterAccessRequestTaskFactory(
        owner=User.objects.get(username=username), process__access_request=access_request
    )


@given('an importer access request "{flow_task}" task owned by "{username}" exists')
def create_importer_access_request_named_task(context, flow_task, username):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.IMPORTER)
    factory.ImporterAccessRequestTaskFactory(
        flow_task=flows.ImporterAccessRequestFlow._meta.node(flow_task),
        owner=User.objects.get(username=username),
        process__access_request=access_request,
    )


@given('an exporter access request "{flow_task}" task owned by "{username}" exists')
def create_exporter_access_request_named_task(context, flow_task, username):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.EXPORTER)
    factory.ExporterAccessRequestTaskFactory(
        flow_task=flows.ExporterAccessRequestFlow._meta.node(flow_task),
        owner=User.objects.get(username=username),
        process__access_request=access_request,
    )


@given("an importer agent access request task exists")
def create_importer_agent_access_request(context):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.IMPORTER_AGENT)
    factory.ImporterAccessRequestTaskFactory(process__access_request=access_request)


@given("an exporter agent access request task exists")
def create_exporter_agent_access_request(context):
    access_request = factory.AccessRequestFactory(request_type=AccessRequest.EXPORTER_AGENT)
    factory.ExporterAccessRequestTaskFactory(process__access_request=access_request)


@given('approval request to importer "{name}" exists for user "{username}"')
def create_importer_approval_request_task(context, name, username):
    importer = Importer.objects.get(name=name)
    access_request = factory.AccessRequestFactory(
        request_type=AccessRequest.IMPORTER, linked_importer=importer
    )
    approval_request = ApprovalRequestFactory(access_request=access_request)
    ApprovalRequestTaskFactory(
        flow_task=ApprovalRequestFlow.respond,
        process__approval_request=approval_request,
        owner=User.objects.get(username=username),
    )


@when('sets access request type to "{text}"')
def set_access_request_type(context, text):
    context.browser.find_element_by_xpath(
        f"//select[@name='request_type']/option[text()='{text}']"
    ).click()


@when('sets access request close response to "{text}"')
def set_access_request_close_response(context, text):
    context.browser.find_element_by_xpath(
        f"//select[@id='id_response']/option[text()='{text}']"
    ).click()


@when('sets approval request response to "{text}"')
def set_approval_request_response(context, text):
    context.browser.find_element_by_xpath(
        f"//select[@id='id_response']/option[text()='{text}']"
    ).click()


@when("the user requests to act as an importer")
def request_importer_access(context):
    utils.go_to_page(context, "access:importer:request")
    option = "Request access to act as an Importer"
    set_access_request_type(context, option)

    fill_organisation_name(context, "some importer")
    fill_organisation_address(context, "1 BDD street\n BBD-000\nLondon")
    fill_request_reason(context, "just testing")
    submit_access_request_form(context)


@when("the user requests to act as an exporter")
def request_exporter_access(context):
    utils.go_to_page(context, "access:exporter:request")
    option = "Request access to act as an Exporter"
    set_access_request_type(context, option)

    fill_organisation_name(context, "some exporter")
    fill_organisation_address(context, "1 BDD street\n BBD-000\nLondon")
    submit_access_request_form(context)


@when("the user requests to act as an agent of an importer")
def request_importer_agent_access(context):
    utils.go_to_page(context, "access:importer:request")
    option = "Request access to act as an Agent for an Importer"
    set_access_request_type(context, option)

    fill_organisation_name(context, "best imports ltd")
    fill_organisation_address(context, "Somewhere")
    fill_request_reason(context, "testing the agent")
    fill_agent_name(context, "best agent for importers ltd.")
    fill_agent_address(context, "next to the buthcer")
    submit_access_request_form(context)


@when("the user requests to act as an agent of an exporter")
def request_exporter_agent_access(context):
    utils.go_to_page(context, "access:exporter:request")
    option = "Request access to act as an Agent for an Exporter"
    set_access_request_type(context, option)

    fill_organisation_name(context, "dude exporters ltd")
    fill_organisation_address(context, "London")
    fill_agent_name(context, "dude export agents ltd.")
    fill_agent_address(context, "Manchester")
    submit_access_request_form(context)


@then("following fields are visible on access request form")
def fields_visible(context):
    for text, is_visible in context.table:
        label = utils.find_element_by_text(context, text, "label")
        assert label, f"label with text {text} not found"

        assert label.is_displayed() == utils.to_boolean(
            is_visible
        ), f"expecting {text} visibility to be {is_visible} but it is {label.is_displayed()}"


@then("a success message is displayed")
def success_message_displayed(context):
    assert utils.find_element_by_text(
        context,
        "Your access request has been submitted to ILB",
        '*/div[contains(@class, "info-box-success") ]/p',
    ), "Success message not found"


@then("there are {count} pending access requests to act as an importer")
def check_pending_importer_requests(context, count):
    elements = context.browser.find_elements_by_css_selector(".pending-import-requests .main-entry")
    element_count = len(elements)

    assert element_count == int(
        count
    ), f"expecting {count} of elements in pending import requests but found {element_count}"


@then("there are {count} pending access requests to act as an exporter")
def check_pending_exporter_requests(context, count):
    elements = context.browser.find_elements_by_css_selector(".pending-export-requests .main-entry")
    element_count = len(elements)

    assert element_count == int(
        count
    ), f"expecting {count} of elements in pending export requests but found {element_count}"
