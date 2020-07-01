from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from django.conf import settings

from web.domains.importer.models import Importer
from web.domains.office.models import Office


def before_scenario(context, scenario):
    context.BASE_URL = f'http://{settings.TEST_SITE_HOST}'

    context.PAGES_MAP = {
        'ICMS homepage': context.BASE_URL,
        'Login page': context.BASE_URL,
        'workbasket': f'{context.BASE_URL}/workbasket',
        'user home': f'{context.BASE_URL}/home',
        'logout': f'{context.BASE_URL}/logout',
        'Request Importer/Exporter Access page':
        f'{context.BASE_URL}/access/request',
        'Importer List page': f'{context.BASE_URL}/importer',
    }

    context.CREATED_USERS = {
        'app-admin': {
            'username': 'app-admin',
            'password': 'app-admin',
            'first_name': 'app-admin',
            'is_superuser': True
        },
        'app-user': {
            'username': 'app-user',
            'password': 'app-user',
            'is_superuser': False
        },
        'app-importer': {
            'username': 'app-importer',
            'password': 'app-importer',
            'first_name': 'app-importer',
            'is_superuser': False
        },
    }

    context.OFFICES = {
        'Elm Street Imports': [
            {
                'is_active': True,
                'postcode': '43001 DreamLand',
                'address': '1428 Elm Street',
                'eori_number': None,
                'address_entry_type': Office.EMPTY,
            },
        ]
    }
    context.IMPORTERS = {
        'Elm Street Imports': {
            'type': Importer.ORGANISATION,
            'name': 'Elm Street Imports',
            'region_origin': Importer.NON_EUROPEAN,
            'is_active': True,
            'offices': context.OFFICES['Elm Street Imports'],
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
