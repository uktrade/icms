from dataclasses import dataclass, field
from typing import Any, TypedDict

from django.conf import settings
from govuk_onelogin_django.constants import ONE_LOGIN_UNSET_NAME

from .constants import DEFAULT_APPLICANT_GREETING


class ImporterDetails(TypedDict):
    id: int
    name: str
    authority_refs: str


@dataclass
class RecipientDetails:
    first_name: str
    email_address: str
    _first_name: str = field(init=False)
    _email_address: str = field(init=False)

    @property  # type: ignore[no-redef]
    def first_name(self) -> str:
        return self._first_name

    @first_name.setter
    def first_name(self, value: str | None) -> None:
        if not value or value == ONE_LOGIN_UNSET_NAME:
            value = DEFAULT_APPLICANT_GREETING
        self._first_name = value

    @property  # type: ignore[no-redef]
    def email_address(self) -> str:
        return self._email_address

    @email_address.setter
    def email_address(self, value: str) -> None:
        """If APP_ENV is local, dev, uat or staging and SEND_ALL_EMAILS_TO is set in django settings all emails will be sent to
        the specified email addresses.
        """
        if (
            settings.APP_ENV in ("local", "dev", "uat", "staging", "hotfix")
            and settings.SEND_ALL_EMAILS_TO
        ):
            self._email_address = settings.SEND_ALL_EMAILS_TO[0]
        else:
            self._email_address = value

    def __hash__(self) -> int:
        """When hashing the object only the email address is used. This is done to allow duplicates to be easily filtered out."""
        return hash(self.email_address)

    def __eq__(self, other: Any) -> bool:
        """When compared to other objects only use the email address. This is done to allow duplicates to be easily filtered out."""
        if isinstance(other, RecipientDetails):
            return self.email_address == other.email_address
        return False
