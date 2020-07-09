from behave import then
from features.steps import utils


@then('workbasket lists importer access request for "{organisation_name}"')
def check_company_access_request(context, organisation_name):
    # TODO: Needs to be reiterated when workbasket feature is done
    # see ICMSLST-16 Workbasket epic
    assert utils.find_element_by_text(
        context, organisation_name, "td"
    ), f"Access Request for {organisation_name} could not be found!"

    assert utils.find_element_by_text(
        context, "Importer Access Request", "td"
    ), 'Access Request type "Importer Access Request could not be found!"'
