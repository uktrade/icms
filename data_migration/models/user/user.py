from typing import Any, Generator

from django.contrib.auth.hashers import make_password
from django.db import models
from django.db.models import F
from django.utils import timezone

from data_migration.models.base import MigrationBase


class User(MigrationBase):
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=20, null=True)
    preferred_first_name = models.CharField(max_length=4000, null=True)
    middle_initials = models.CharField(max_length=40, null=True)
    organisation = models.CharField(max_length=4000, null=True)
    department = models.CharField(max_length=4000, null=True)
    job_title = models.CharField(max_length=320, null=True)
    location_at_address = models.CharField(max_length=4000, null=True)
    work_address = models.CharField(max_length=300, null=True)
    date_of_birth = models.DateField(null=True)
    security_question = models.CharField(max_length=4000, null=True)
    security_answer = models.CharField(max_length=4000, null=True)
    share_contact_details = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, null=False)
    account_status_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    account_status_date = models.DateField(null=True)
    password_disposition = models.CharField(max_length=20, null=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)


class Importer(MigrationBase):
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=20)
    name = models.TextField(null=True)
    registered_number = models.CharField(max_length=15, null=True)
    eori_number = models.CharField(max_length=20, null=True)
    eori_number_ni = models.CharField(max_length=20, null=True)
    region_origin = models.CharField(max_length=1, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    comments = models.TextField(null=True)
    main_importer = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)
        data["name"] = data["name"] or ""
        return data


class Office(MigrationBase):
    importer = models.ForeignKey(Importer, on_delete=models.CASCADE)
    legacy_id = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(null=False, default=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=4000, null=True)
    eori_number = models.CharField(max_length=20, null=True)
    address_entry_type = models.CharField(max_length=10, null=False, default="EMPTY")

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["importer_id"]

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        # TODO ICMSLST-1689 - This will need to be reworked for exporter offices
        return cls.objects.values("importer_id", "id", office_id=F("id")).iterator()
