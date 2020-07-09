from behave import when
from features.steps import utils
from selenium.webdriver.common.by import By


@when("the user clicks on logout button")
def click_on_logout(context):
    utils.go_to_page(context, "home")
    context.browser.find_element(By.ID, "btnLogout").click()
