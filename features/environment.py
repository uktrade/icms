from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from django.conf import settings


def before_scenario(context, scenario):
    context.BASE_URL = f'http://{settings.TEST_SITE_HOST}'

    context.PAGES_MAP = {
        'ICMS homepage': context.BASE_URL,
        'Login page': context.BASE_URL,
        'workbasket': f'{context.BASE_URL}/workbasket',
    }

    context.CREATED_USERS = {
        'app-user': {
            'username': 'app-user',
            'password': 'app-user'
        }
    }


def after_feature(context, feature):
    context.browser.quit()


def before_feature(context, feature):
    browser = DesiredCapabilities.CHROME
    if 'firefox' == settings.SELENIUM_BROWSER:
        browser = DesiredCapabilities.FIREFOX

    context.browser = webdriver.Remote(
        command_executor=f"http://{settings.SELENIUM_HUB_HOST}/wd/hub",
        desired_capabilities=browser,
    )
    context.browser.implicitly_wait(5)
