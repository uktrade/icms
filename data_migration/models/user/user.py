from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils import timezone

from data_migration.models.base import MigrationBase


class User(MigrationBase):
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=20, blank=False, null=True)
    preferred_first_name = models.CharField(max_length=4000, blank=True, null=True)
    middle_initials = models.CharField(max_length=40, blank=True, null=True)
    organisation = models.CharField(max_length=4000, blank=False, null=True)
    department = models.CharField(max_length=4000, blank=False, null=True)
    job_title = models.CharField(max_length=320, blank=False, null=True)
    location_at_address = models.CharField(max_length=4000, blank=True, null=True)
    work_address = models.CharField(max_length=300, blank=False, null=True)
    date_of_birth = models.DateField(null=True)
    security_question = models.CharField(max_length=4000, blank=False, null=True)
    security_answer = models.CharField(max_length=4000, blank=False, null=True)
    share_contact_details = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, blank=False, null=False)
    account_status_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    account_status_date = models.DateField(null=True)
    password_disposition = models.CharField(max_length=20, blank=True, null=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)


class Importer(MigrationBase):
    is_active = models.BooleanField(default=True)
    type = models.CharField(max_length=20)
    name = models.TextField(blank=True, default="")
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    eori_number = models.CharField(max_length=20, blank=True, null=True)
    eori_number_ni = models.CharField(max_length=20, blank=True, null=True)
    region_origin = models.CharField(max_length=1, blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
    )
    comments = models.TextField(blank=True, null=True)
    main_importer = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="+"
    )


class Office(MigrationBase):
    is_active = models.BooleanField(blank=False, null=False, default=True)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=4000, blank=False, null=True)
    eori_number = models.CharField(max_length=20, blank=True, null=True)
    address_entry_type = models.CharField(max_length=10, blank=False, null=False, default="EMPTY")
