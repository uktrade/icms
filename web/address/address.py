import requests
import structlog as logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from web.errors import ICMSException, UnknownError

logger = logging.getLogger(__name__)


def find(post_code):
    post_code = post_code.replace(" ", "")
    URL = "https://api.getaddress.io/find/{}?expand=true".format(post_code)
    logger.debug("Searching for postcode: %s", post_code)
    response = requests.get(URL.format(post_code), auth=("api-key", settings.ADDRESS_API_KEY))

    if response.status_code == 200:
        address = response.json()["addresses"]
        return address

    error_message = response.json()["Message"]

    logger.debug("Postcode seach error: %s", error_message)
    logger.debug(response)

    # Errors
    if response.status_code == 404:
        return []
    elif response.status_code == 400:
        raise ICMSException(error_message)
    elif response.status_code == 401:
        raise ImproperlyConfigured("Invalid api key")

    raise UnknownError(error_message)
