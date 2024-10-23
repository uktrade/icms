import os
import traceback
from typing import Literal

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
        enable_tracing=True,
        sample_rate=0.01,
        traces_sample_rate=0.01,  # reduce the number of performance traces
        enable_backpressure_handling=True,  # ensure that when sentry is overloaded, we back off and wait
        release=os.getenv("GIT_TAG"),
    )

    global sentry_initialized
    sentry_initialized = True


def capture_message(
    msg: str, level: Literal["fatal", "critical", "error", "warning", "info", "debug"] = "info"
) -> None:
    """If Sentry is enabled, log the given message, otherwise print it to the console.

    :param msg: message to capture
    :param level: message level
    """

    if sentry_initialized:
        sentry_sdk.capture_message(msg, level=level)
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
