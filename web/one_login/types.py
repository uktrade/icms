from typing import TypedDict


class UserInfo(TypedDict):
    # https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/integrate-with-code-flow/#receive-response-for-retrieve-user-information
    # openid scope
    sub: str
    # email scope
    email: str
    email_verified: bool


class UserCreateData(TypedDict):
    email: str
    first_name: str
    last_name: str
