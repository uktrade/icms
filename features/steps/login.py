from behave import then, when
from selenium.webdriver.common.by import By

from features.steps import utils


@when('"{username}" attempts login with invalid credentials')
def user_login_invalid_credentials(context, username):
    return utils.login(context, username, 'wrong-password')


@when('"{username}" attempts login')
def attemp_login(context, username):
    return utils.login(context, username, 'wrong-password')


@then('an invalid credentials message is displayed')
def login_error_is_displayed(context):
    try:
        assert context.browser.find_element(
            By.ID, 'login-error'), "Login Error Message Not Found"
        assert 'Invalid username or password' in context.browser.find_element(
            By.ID, 'login-error'
        ).text, "Login Error Message Is not the one we expected"
    except Exception as e:
        raise e
