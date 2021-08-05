import os
import traceback

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# has sentry been initialized
sentry_initialized = False


def init_sentry() -> None:
    """Initialize Sentry client."""

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        environment=os.environ.get("SENTRY_ENVIRONMENT"),
        integrations=[DjangoIntegration()],
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
        traceback.print_exc()
