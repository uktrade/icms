import datetime as dt

from pydantic import BaseModel


class UserSerializer(BaseModel):
    id: int
    title: str | None
    first_name: str
    last_name: str
    email: str
    primary_email_address: str | None
    organisation: str | None
    department: str | None
    job_title: str | None
    date_joined: dt.datetime | None
    last_login: dt.datetime | None
    exporter_ids: list[int]
    importer_ids: list[int]
    group_names: list[str | None]


class Users(BaseModel):
    users: list[UserSerializer]
