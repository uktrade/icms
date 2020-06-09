from behave import then, when, given
from web.tests.domains.importer.factory import ImporterFactory
from web.domains.importer.models import Importer
from selenium.webdriver.support.ui import Select


@given(u'An importer with status "{imp_status}" is created in the system')  # NOQA: F811
def step_impl(context, imp_status):
    if imp_status.lower() == 'draft':
        status = Importer.DRAFT

    if imp_status.lower() == 'current':
        status = Importer.CURRENT

    if imp_status.lower() == 'archived':
        status = Importer.ARCHIVED

    ImporterFactory(
        name=f'{imp_status} Importer',
        type=Importer.ORGANISATION,
        status=status,
        is_active=True
    )


@when(u'the user selects to filter importers with status "{imp_status}"')  # NOQA: F811
def step_impl(context, imp_status):
    if imp_status.lower() == "any":
        imp_status = ""
    select = Select(context.browser.find_element_by_id('id_status'))
    select.select_by_value(imp_status.upper())


@when(u'submits the import search from')  # NOQA: F811
def step_impl(context):
    context.browser.find_element_by_id('btn-submit-search').click()


@then(u'the importer search results contain "{count}" results')  # NOQA: F811
def step_impl(context, count):
    elements = context.browser.find_elements_by_css_selector('#tbl-search-results .result-row')
    element_count = len(elements)

    assert element_count == int(count), f'expecting {count} of elements in search results but found {element_count}'


@then(u'the result at row "{row}" has the name "{name}"')  # NOQA: F811
def step_impl(context, row, name):
    element = context.browser.find_element_by_css_selector(f'#tbl-search-results .result-row:nth-child({int(row)}) td:nth-child(1)')

    assert name in element.text, f'could not find {name} in {element.text}'


@then(u'the result at row "{row}" has the status "{status}"')  # NOQA: F811
def step_impl(context, row, status):
    element = context.browser.find_element_by_css_selector(f'#tbl-search-results .result-row:nth-child({int(row)}) td:nth-child(2)')

    assert status.lower() in element.text.lower(), f'could not find {status} in {element.text}'
