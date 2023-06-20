from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F, Value
from django.db.models.expressions import Window
from django.db.models.functions import Concat, RowNumber
from django.utils import timezone

from data_migration.models.base import MigrationBase
from data_migration.utils.format import split_address


class User(MigrationBase):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    salt = models.CharField(max_length=16, null=True)
    encrypted_password = models.CharField(max_length=32, null=True)
    last_login_datetime = models.DateTimeField(null=True)
    date_joined_datetime = models.DateTimeField(default=timezone.now)
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
    account_status = models.CharField(max_length=20)
    account_status_by = models.CharField(max_length=255, null=True)
    account_status_date = models.DateField(null=True)
    password_disposition = models.CharField(max_length=20, null=True)
    unsuccessful_login_attempts = models.PositiveSmallIntegerField(default=0)
    email_address_xml = models.TextField(null=True)
    telephone_xml = models.TextField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "salt",
            "encrypted_password",
            "last_login_datetime",
            "date_joined_datetime",
            #
            # User fields removed in V2 model
            #
            "preferred_first_name",
            "middle_initials",
            "security_question",
            "security_answer",
            "share_contact_details",
            "account_status",
            "account_status_by",
            "account_status_date",
            "password_disposition",
            "unsuccessful_login_attempts",
        ]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "last_login": F("last_login_datetime"),
            "date_joined": F("date_joined_datetime"),
            "password": Concat(
                Value("fox_pbkdf2_sha1$10000$"),
                "id",
                Value(":"),
                "salt",
                Value("$"),
                "encrypted_password",
                output_field=models.CharField(),
            ),
        }

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()
        related = cls.get_related()
        return (
            cls.objects.select_related(*related)
            .exclude(pk=0)
            .order_by("pk")
            .values(*values, **values_kwargs)
            .iterator(chunk_size=2000)
        )

    # M2M groups / user permissions


class PhoneNumber(MigrationBase):
    phone = models.CharField(max_length=60)
    type = models.CharField(max_length=30)
    comment = models.CharField(max_length=4000, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_numbers")


class AlternativeEmail(MigrationBase):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alternative_emails")
    email = models.EmailField(max_length=254)
    type = models.CharField(max_length=30)
    portal_notifications = models.BooleanField(default=False)
    comment = models.CharField(max_length=4000, null=True)


class PersonalEmail(MigrationBase):
    is_primary = models.BooleanField(blank=False, null=False, default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personal_emails")
    email = models.EmailField(max_length=254)
    type = models.CharField(max_length=30)
    portal_notifications = models.BooleanField(default=False)
    comment = models.CharField(max_length=4000, null=True)


class Importer(MigrationBase):
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=20)
    name = models.TextField(null=True)
    registered_number = models.CharField(max_length=15, null=True)
    eori_number = models.CharField(max_length=20, null=True)
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


class Exporter(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    name = models.TextField()
    registered_number = models.CharField(max_length=15, null=True)
    comments = models.TextField(null=True)
    main_exporter = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="agents"
    )


class Office(MigrationBase):
    importer = models.ForeignKey(Importer, on_delete=models.CASCADE, null=True)
    exporter = models.ForeignKey(Exporter, on_delete=models.CASCADE, null=True)
    legacy_id = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(null=False, default=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=4000, null=True)
    eori_number = models.CharField(max_length=20, null=True)
    address_entry_type = models.CharField(max_length=10, null=False, default="EMPTY")

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        m2m_id = f"{target._meta.model_name}_id"

        return (
            cls.objects.exclude(**{f"{m2m_id}__isnull": True})
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                m2m_id,
                office_id=F("id"),
            )
            .iterator(chunk_size=2000)
        )

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)

        importer = data.pop("importer_id")
        exporter = data.pop("exporter_id")

        if importer:
            # Some extra data is in some postcode fields from a previous data migration
            # Postcodes can be a max of 8 characters
            postcode = data.pop("postcode")
            postcode = postcode and postcode.strip()[-8:]
            data["postcode"] = postcode

        elif exporter:
            # Exporters with long postcodes need postcode added to address field and postcode nullified
            if len(data["postcode"] or "") > 8:
                postcode = data.pop("postcode")
                data["address"] = data["address"] + "\n" + postcode

        # Addresses are split one field per line in V2
        address = data.pop("address")

        return data | split_address(address)

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data
