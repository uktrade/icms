from typing import Any

import requests
from django.conf import settings

from web.errors import APIError


def api_postcode_to_address_lookup(post_code: str) -> list[dict[str, Any]]:
    """Return addresses related to the postcode.

    Documentation: https://documentation.getaddress.io/
    """
    api_url = f"https://api.getAddress.io/find/{post_code}"

    payload = {"api-key": settings.ADDRESS_API_KEY, "expand": True, "sort": True}
    response = requests.get(api_url, params=payload)

    if response.status_code == 200:
        content = response.json()

        return content["addresses"]

    default_user_error = "Unable to lookup postcode"

    # The documented error codes from getaddress.io
    known_error_codes = {
        400: "The postcode is invalid",  # Your postcode is not valid.
        401: default_user_error,  # Your api-key is not valid.
        403: default_user_error,  # Your api-key is valid but you do not have permission to access to the resource.
        429: default_user_error,  # You have made more requests than your allowed limit.
        404: "Unable to find addresses for this postcode",  # No addresses could be found for this postcode.
        500: default_user_error,  # Server error, you should never see this.
    }

    content = response.json()
    error_msg = known_error_codes.get(response.status_code, default_user_error)
    dev_error = content["Message"]

    raise APIError(
        error_msg=error_msg,
        dev_error_msg=f"status_code: {response.status_code}: error: {dev_error}",
        status_code=response.status_code,
    )
