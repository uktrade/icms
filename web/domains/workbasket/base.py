import datetime as dt
from dataclasses import dataclass, field


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
    confirm: str | None = None

    # Optional section label
    # Used to group actions of import / export applications
    section_label: str | None = None


@dataclass
class WorkbasketSection:
    information: str
    actions: list[WorkbasketAction]


@dataclass
class WorkbasketRow:
    """Note that none of the fields are optional, they're just marked so to make
    constructing these items easier."""

    id: int | None = None

    # transaction / reference number
    reference: str | None = None

    # subject / topic
    subject: str | None = None

    # importer/exporter/etc name
    company: str | None = None

    # agent name
    company_agent: str | None = None

    # status
    status: str | None = None

    timestamp: dt.datetime | None = None

    # admin/applicant/etc actions go into their own block
    sections: list[WorkbasketSection] = field(default_factory=list)
