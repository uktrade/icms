from behave import then, when
from selenium.webdriver.common.by import By
from features.steps.shared import user_login


@then(u'the login page is displayed')
def login_page_is_displayed(context):
    needle = "Log in to ICMS"
    result = context.browser.find_elements(By.XPATH, '//*[contains(text(),"%s")]' % needle)

    assert len(result) > 0, 'Not on Login Page'


@then(u'an invalid login message is visible')
def login_error_is_displayed(context):
    try:
        assert context.browser.find_element(By.ID, 'login-error'), "Login Error Message Not Found"
        assert 'Invalid username or password' in context.browser.find_element(By.ID, 'login-error').text, "Login Error Message Is not the one we expected"
    except Exception as e:
        raise e


@when(u'the user "{user}" logs in with invalid credentials')
def user_login_invalid_credentials(context, user):
    return user_login(context, user, 'wrong-password')
