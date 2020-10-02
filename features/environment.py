from django.conf import settings

from behave_django.testcase import BehaviorDrivenTestCase
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


def before_scenario(context, scenario):
    BehaviorDrivenTestCase.host = settings.SELENIUM_HOST


def after_feature(context, feature):
    context.browser.quit()


def configure(context):
    browser = DesiredCapabilities.CHROME
    if "firefox" == settings.SELENIUM_BROWSER:
        browser = DesiredCapabilities.FIREFOX

    context.browser = webdriver.Remote(
        command_executor=f"http://{settings.SELENIUM_HUB_HOST}:4444/wd/hub",
        desired_capabilities=browser,
    )
    context.browser.implicitly_wait(5)


def before_feature(context, feature):
    configure(context)
    # Load permission data
    context.fixtures = ["permissions.yaml"]


def after_step(context, step):
    if step.status == "failed":
        context.browser.save_screenshot(
            f"/code/test-reports/bdd-screenshots/{context.scenario.name}-{step.name}.png"
        )
