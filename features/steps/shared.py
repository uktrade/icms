from behave import given, when, then
from selenium.webdriver.common.by import By

from web.tests.domains.user.factory import UserFactory
from web.models import User


@when(u'the user "{user}" logs in')
@given(u'the user "{user}" logs in')
def user_logs_in(context, user):
    given_the_user_is_created(context, user)
    user_navigates_to_page(context, 'Login page')

    user_data = context.CREATED_USERS[user]
    user_login(context, user_data['username'], user_data['password'])


@when(u'the user logs in with {username} and {password}')
def user_login(context, username, password):
    username_field = context.browser.find_element(By.ID, 'id_username')
    password_field = context.browser.find_element(By.ID, 'id_password')
    submit_button = context.browser.find_element(By.XPATH, '//button[contains(text(),"Sign in")]')

    username_field.send_keys(username)
    password_field.send_keys(password)
    submit_button.click()


@given(u'an anonymous user navigates to {page}')
@given(u'the user navigates to "{page}"')
@when(u'the user navigates to "{page}"')
def user_navigates_to_page(context, page):
    context.browser.get(context.PAGES_MAP[page])


@given(u'The user "{user}" is created in the system')
def given_the_user_is_created(context, user):
    assert user in context.CREATED_USERS, f'User {user} not configured, add it to context.CREATED_USERS'

    user = context.CREATED_USERS[user]
    UserFactory(
        username=user['username'],
        password=user['password'],
        first_name=user['first_name'] or user['username'],
        password_disposition=User.FULL,
        is_superuser=False,
        account_status=User.ACTIVE,
        is_active=True
    )


@then(u'the "{page}" page is displayed')
def the_page_is_displayed(context, page):

    assert page in context.PAGES_MAP, f'{page} alias not defined, add it to context.PAGES_MAP'

    page_url = context.browser.current_url.strip('/')
    expected_url = context.PAGES_MAP[page].strip('/')
    assert expected_url == page_url, f'expecting url to be {expected_url} but got {page_url}'

@then(u'the text "{text}" is visible')
def text_is_visible(context, text):
    assert find_element_with_text(context, text), f'could not find text {text} in page'


@then(u'a button with text "{text}" is visible')
def button_with_text_is_visible(context, text):
    find_element_with_text(context, text, 'button')


## utils

def find_element_with_text(context, text, element='*'):
    try:
        return context.browser.find_element(By.XPATH, f'//{element}[contains(text(),"{text}")]')
    except Exception as e:
        print(e)
        return None


def to_boolean(str):
    return str.lower() in ['true', '1', 't', 'y', 'yes']