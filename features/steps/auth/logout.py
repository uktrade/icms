from behave import then, when
from selenium.webdriver.common.by import By
from features.steps.shared import user_navigates_to_page
from features.steps.auth.login import login_page_is_displayed


@when(u'the user click on logout button')
def click_on_logout(context):
    context.browser.find_element(By.ID, 'btnLogout').click()


@then(u'the user is logged out')
def user_is_logged_out(context):
    # try to navigate to workbasket
    # ensure the login page is displayed
    user_navigates_to_page(context, 'workbasket')
    login_page_is_displayed(context)
