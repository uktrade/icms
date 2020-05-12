from behave import given


@given(u'an {user} user navigates to {page}')
def user_navigates_to_page(context, user, page):
    context.browser.get(context.PAGES_MAP[page])
