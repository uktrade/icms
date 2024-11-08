from django.db import models
from django.utils import timezone

from data_migration.models.base import MigrationBase


class User(MigrationBase):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    salt = models.CharField(max_length=16, null=True)
    encrypted_password = models.CharField(max_length=32, null=True)

    # Datetime TZ formatting looks for fields named _datetime
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
    personal_email_xml = models.TextField(null=True)
    alternative_email_xml = models.TextField(null=True)
    telephone_xml = models.TextField(null=True)


class PhoneNumber(MigrationBase):
    phone = models.CharField(max_length=60)
    type = models.CharField(max_length=30)
    comment = models.CharField(max_length=4000, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_numbers")


class Email(MigrationBase):
    is_primary = models.BooleanField(blank=False, null=False, default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="emails")
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


class Exporter(MigrationBase):
    is_active = models.BooleanField(default=True)
    name = models.TextField()
    registered_number = models.CharField(max_length=15, null=True)
    comments = models.TextField(null=True)
    main_exporter = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="agents"
    )
    exclusive_correspondence = models.BooleanField(default=False)


class Office(MigrationBase):
    importer = models.ForeignKey(Importer, on_delete=models.CASCADE, null=True)
    exporter = models.ForeignKey(Exporter, on_delete=models.CASCADE, null=True)
    legacy_id = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=4000, null=True)
    eori_number = models.CharField(max_length=20, null=True)
    address_entry_type = models.CharField(max_length=10, null=False, default="EMPTY")
