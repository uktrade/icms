import enum
from typing import TypedDict


class UserInfo(TypedDict):
    # https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/authenticate-your-user/#retrieve-user-information
    # openid scope
    sub: str
    # email scope
    email: str
    email_verified: bool


class UserCreateData(TypedDict):
    email: str
    first_name: str
    last_name: str


# https://docs.sign-in.service.gov.uk/before-integrating/choose-the-level-of-authentication/
class AuthenticationLevel(enum.StrEnum):
    # Username and Password
    LOW_LEVEL = "Cl"
    # LOW_LEVEL & two-factor authentication
    MEDIUM_LEVEL = "Cl.Cm"


# https://docs.sign-in.service.gov.uk/before-integrating/choose-the-level-of-identity-confidence/
class IdentityConfidenceLevel(enum.StrEnum):
    NONE = "P0"
    LOW = "P1"
    MEDIUM = "P2"
