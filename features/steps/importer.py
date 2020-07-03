import re

from behave import given, then, when
from features.steps import utils
from selenium.webdriver.support.ui import Select
from web.domains.importer.models import Importer
from web.domains.user.models import User
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory


@given('importer "{name}" exists')
def create_importer(context, name):
    ImporterFactory(name=name, is_active=True)


@given('individual importer "{importer_name}" exists with user "{user_name}"')
def create_individual_importer(context, importer_name, user_name):
    # individual importers in real life have an empty name field, but the BDD tests
    # won't work like that since statements like 'Jane" is an agent of "Hey Ltd"'
    # wouldn't work, we need somethign to match against.
    #
    # so give them a name, but link them to a user.
    user = User.objects.get(username=user_name)
    ImporterFactory(name=importer_name, type=Importer.INDIVIDUAL, is_active=True, user=user)


@given('archived importer "{name}" exists')
def create_archived_importer(context, name):
    ImporterFactory(name=name, is_active=False)


@given('non-European importer "{name}" exists')
def create_non_european_importer(context, name):
    ImporterFactory(name=name,
                    region_origin=Importer.NON_EUROPEAN,
                    is_active=True)


@given('import organisation "{name}" exists')
def create_import_organisation(context, name):
    ImporterFactory(name=name, type=Importer.ORGANISATION, is_active=True)


@given(
    'importer "{name}" has an office with address "{address}" and postcode "{postcode}"'
)
def create_importer_office(context, name, address, postcode):
    importer = Importer.objects.get(name=name)
    importer.offices.add(
        OfficeFactory(is_active=True, address=address, postcode=postcode))


@given(
    '"{agent_name}" is an agent of "{importer_name}"'
)
def mark_as_agent(context, agent_name, importer_name):
    agent = Importer.objects.get(name=agent_name)
    importer = Importer.objects.get(name=importer_name)

    agent.main_importer = importer
    agent.save()


@when('clicks on importer name "{name}"')
def clicks_on_importer_name(context, name):
    utils.find_element_by_text(context, name,
                               "a[@role = 'model-link']").click()


@when('views importer "{name}"')
def views_importer(context, name):
    importer = Importer.objects.get(name=name)
    utils.go_to_page(context, 'importer-view', pk=importer.pk)


@when('edits importer "{name}"')
def edits_importer(context, name):
    importer = Importer.objects.get(name=name)
    utils.go_to_page(context, 'importer-edit', pk=importer.pk)


@when('"{username}" edits importer "{name}"')
def user_edits_importer(context, username, name):
    edits_importer(context, name)


@when('"{username}" views importer "{name}"')
def user_views_importer(context, username, name):
    views_importer(context, name)


@when('clicks on the back link')
def click_back_link(context):
    context.browser.find_element_by_css_selector(
        'main #content a.prev-link').click()


@when('filters importers by status "{status}"')
def filter_importer_by_status(context, status):
    value = ""
    if status.lower() == "archived":
        value = "False"

    if status.lower() == "current":
        value = "True"

    select = Select(context.browser.find_element_by_id('id_status'))
    select.select_by_value(value)
    context.browser.find_element_by_id('btn-submit-search').click()


@when('clicks on add office')
def click_importer_add_office(context):
    context.browser.find_element_by_id('btn-add-office').click()


@when('enters address "{address}"')
def enters_importer_address(context, address):
    context.browser.find_element_by_css_selector(
        '.new-form-row:last-child textarea').send_keys(address)


@when('enters postcode "{postcode}"')
def enters_importer_postcode(context, postcode):
    context.browser.find_element_by_css_selector(
        '.new-form-row:last-child textarea').send_keys(postcode)


@when('submits importer edit form')
def submit_importer_edit(context):
    context.browser.find_element_by_id('btn-submit').click()


@then('importer "{name}" is in the list')
def check_importer_in_list(context, name):
    assert utils.find_element_by_text(
        context, name,
        "a[@role = 'model-link']"), 'importer {name} is not in the list'


@then('"{url_name}" page for importer "{name}" is displayed')
def importer_page_displayed(context, url_name, name):
    importer = Importer.objects.get(name=name)
    utils.assert_on_page(context, url_name, pk=importer.pk)


@then('importer name reads "{expected_name}"')
def importer_name_reads(context, expected_name):
    name_field = context.browser.find_element_by_css_selector(
        'form [data-label="Name"]')
    assert name_field.text == expected_name, f'expecting importer name to read "{expected_name}" but got "{name_field.text}"'


@then('importer details read as follows')
def importer_details_read(context):
    for field, value in context.table:
        found_value = context.browser.find_element_by_css_selector(
            f'[data-label="{field}"]').text
        assert value == found_value, f'expecting field "{field}" to be "{value}" but got "{found_value}"'


@then('importer edit fields read as follows')
def importer_edit_form_reads(context):
    for field, value in context.table:
        id = f'#id_{field.lower().replace(" ","_")}'

        if field == 'Type' or field == 'Region origin':
            found_value = (Select(
                context.browser.find_element_by_css_selector(id))
                           ).first_selected_option.text
        else:
            found_value = context.browser.find_element_by_css_selector(
                id).get_attribute('value')
        assert value == found_value, f'expecting field "{field}" to be "{value}" but got "{found_value}"'


@then('importer offices read as follows')
def importer_offices_read(context):
    context.browser.find_element_by_id('tg-offices-CURRENT').click()
    field_map = {  # field name to table column mapping
        'Address': 1,
        'Post Code': 2,
        'ROI': 3
    }
    for row, field, value in context.table:
        assert field in field_map, f'Unknown Office field {field}'
        column = field_map[field]

        selector = f'.tab-content[data-tab-group="tg-offices"][data-tab-key="CURRENT"] table tr:nth-child({row}) td:nth-child({column})'
        found_value = context.browser.find_element_by_css_selector(
            selector).text
        assert value == found_value, f'expecting to find "{value}" but got "{found_value}"'


@then('importer agents read as follows')
def importer_agents_read(context):
    context.browser.find_element_by_id('tg-agents-CURRENT').click()

    # field name to table column mapping
    field_map = {
        'Importer Name / Importer Entity Type': 1,
        'Agent Type': 2,
        'Address': 3
    }

    for row, field, value in context.table:
        assert field in field_map, f'Unknown Agent field {field}'
        column = field_map[field]

        selector = f'.tab-content[data-tab-group="tg-agents"][data-tab-key="CURRENT"] table tr:nth-child({row}) td:nth-child({column})'
        found_value = context.browser.find_element_by_css_selector(selector).text
        assert re.match(value, found_value), f'expecting to match "{value}" but got "{found_value}"'


@then('no archived importer agents are displayed')
def no_archived_importer_agents_displayed(context):
    context.browser.find_element_by_id('tg-agents-ARCHIVED').click()
    selector = '.tab-content[data-tab-group="tg-agents"][data-tab-key="ARCHIVED"] table tr:nth-child(1) td:nth-child(1)'
    value = "There are no agents"
    found_value = context.browser.find_element_by_css_selector(selector).text
    assert value == found_value, f'expecting to find "{value}" but got "{found_value}"'


@then('importer edit offices read as follows')
def importer_edit_offices_read(context):
    field_map = {  # field name to table column mapping
        'Status': 1,
        'Address': 2,
        'Post Code': 3,
        'ROI': 4
    }
    for row, field, value in context.table:
        assert field in field_map, f'Unknown Office field {field}'
        column = field_map[field]

        selector = f'#tbl-offices tr:nth-child({row}) td:nth-child({column})'
        found_value = context.browser.find_element_by_css_selector(
            selector).text
        assert value == found_value, f'expecting to find "{value}" but got "{found_value}"'


@then('no archived importer office is displayed')
def no_archived_importer_offices_displayed(context):
    context.browser.find_element_by_id('tg-offices-ARCHIVED').click()
    selector = '.tab-content[data-tab-group="tg-offices"][data-tab-key="ARCHIVED"] table tr:nth-child(1) td:nth-child(1)'
    value = "There are no offices"
    found_value = context.browser.find_element_by_css_selector(selector).text
    assert value == found_value, f'expecting to find "{value}" but got "{found_value}"'


@then('importer search has "{count}" results')
def check_importer_results_colunt(context, count):
    elements = context.browser.find_elements_by_css_selector(
        '#tbl-search-results .result-row')
    element_count = len(elements)

    assert element_count == int(
        count
    ), f'expecting {count} of elements in search results but found {element_count}'


@then('importer name at row "{row}" is "{name}"')
def check_importer_name_at_row(context, row, name):
    element = context.browser.find_element_by_css_selector(
        f'#tbl-search-results .result-row:nth-child({int(row)}) td:nth-child(2)'
    )

    assert name in element.text, f'could not find {name} in {element.text}'


@then('importer status at row "{row}" is "{status}"')  # NOQA: F811
def check_importer_status_at_row(context, row, status):
    element = context.browser.find_element_by_css_selector(
        f'#tbl-search-results .result-row:nth-child({int(row)}) td:nth-child(1)'
    )
    assert status.lower() in element.text.lower(
    ), f'could not find {status} in {element.text}'


@then('importer at row "{row}" has action "{action}"')
def check_action_at_row(context, row, action):
    context.browser.find_element_by_css_selector(
        f'#tbl-search-results .result-row:nth-child({int(row)}) td:nth-child(4) [data-input_action="{action}"]'
    )


@then('the result at row "{row}" has the address "{address}"')  # NOQA: F811
def step_impl(context, row, address):
    element = context.browser.find_element_by_css_selector(
        f'#tbl-search-results .result-row:nth-child({int(row)}) td:nth-child(3)'
    )
    assert address.lower() in element.text.lower(
    ), f'could not find {address} in {element.text}'


@then('importer edit offices form shows error "{error}"')
def check_importer_office_errror(context, error):
    el = context.browser.find_element_by_css_selector(
        '#id_form-0-address + .error-message')

    assert error == el.text
