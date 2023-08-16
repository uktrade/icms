from typing import Literal, TypedDict


class AppConfig(TypedDict):
    key: str
    url: str
    name: str


# https://github.com/uktrade/staff-sso/blob/master/sso/user/serializers.py#L13
class StaffSSOProfile(TypedDict):
    email: str
    user_id: str
    email_user_id: str
    first_name: str
    last_name: str
    related_emails: list[str]
    contact_email: str
    groups: list
    permitted_applications: list[AppConfig]
    access_profiles: list[str]
    application_permissions: list[str]


# ICMS uses "email_user_id"
STAFF_SSO_ID = Literal["user_id", "email_user_id"]
