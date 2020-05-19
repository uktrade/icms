from behave import given
from web.tests.domains.user.factory import UserFactory
from web.models import User


@given(u'an {user} user navigates to {page}')
def user_navigates_to_page(context, user, page):
    context.browser.get(context.PAGES_MAP[page])


@given(u'The user "{user}" is created in the system')
def given_the_user_is_created(context, user):
    assert user in context.CREATED_USERS, f'User {user} not configured, add it to context.CREATED_USERS'

    user = context.CREATED_USERS[user]
    UserFactory(
        username=user['username'],
        password=user['password'],
        password_disposition=User.FULL,
        is_superuser=False,
        account_status=User.ACTIVE,
        is_active=True
    )
