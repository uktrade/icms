import datetime
from dataclasses import dataclass, field
from typing import Optional

from web.domains.user.models import User


@dataclass
class WorkbasketAction:
    # GET/POST
    is_post: bool

    # URL
    url: str

    # link name
    name: str

    # execute and process the action in the browser (GET only)
    is_ajax: bool = False

    # confirmation popup text
    confirm: Optional[str] = None

    # Optional section label
    # Used to group actions of import / export applications
    section_label: Optional[str] = None


@dataclass
class WorkbasketSection:
    information: str
    actions: list[WorkbasketAction]


@dataclass
class WorkbasketRow:
    """Note that none of the fields are optional, they're just marked so to make
    constructing these items easier."""

    id: Optional[int] = None

    # transaction / reference number
    reference: Optional[str] = None

    # subject / topic
    subject: Optional[str] = None

    # importer/exporter/etc name
    company: Optional[str] = None

    # agent name
    company_agent: Optional[str] = None

    # status
    status: Optional[str] = None

    # not sure whether this is create or last-update time
    timestamp: Optional[datetime.datetime] = None

    # not clear to me how this is different to status...
    # information: Optional[str] = None

    # admin/applicant/etc actions go into their own block
    sections: list[WorkbasketSection] = field(default_factory=list)


class WorkbasketBase:
    """Base class for every Process subclass that wants to be shown in the workbasket."""

    def get_workbasket_row(self, user: User, is_ilb_admin: bool) -> WorkbasketRow:
        """Get data to show in the workbasket."""

        raise NotImplementedError
