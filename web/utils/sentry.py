import traceback

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# has sentry been initialized
sentry_initialized = False


def init_sentry(sentry_dsn: str, sentry_environment: str) -> None:
    """Initialize Sentry client."""

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_environment,
        integrations=[DjangoIntegration(), RedisIntegration()],
    )

    global sentry_initialized
    sentry_initialized = True


def capture_message(msg: str) -> None:
    """If Sentry is enabled, log the given message, otherwise print it to the console.

    :param msg: message to capture
    """

    if sentry_initialized:
        sentry_sdk.capture_message(msg)
    else:
        print("Sentry::capture_message: %s" % msg)


def capture_exception() -> None:
    """If Sentry is enabled log the active exception, otherwise print it to the
    console."""

    if sentry_initialized:
        sentry_sdk.capture_exception()
    else:
        print("Sentry::capture_exception:")
        traceback.print_exc()
