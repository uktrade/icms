from web.utils.api.auth import APIType, HTTPMethod, make_hawk_sender

JSON_TYPE = "application/json"
# This has to match the request, because it is used to calculate the request's
# Hawk MAC digest.
SERVER_NAME = "caseworker"


def make_testing_hawk_sender(method: HTTPMethod, url: str, api_type: APIType = "hmrc", **kwargs):
    url = f"http://{SERVER_NAME}{url}"

    return make_hawk_sender(method, url, api_type=api_type, **kwargs)
