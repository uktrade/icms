from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from guardian.core import ObjectPermissionChecker
from guardian.mixins import GuardianUserMixin


class User(GuardianUserMixin, AbstractUser):
    def __init__(self, *args, **kwargs):
        self.guardian_checker: ObjectPermissionChecker | None = None

        super().__init__(*args, **kwargs)

    def set_guardian_checker(self):
        """Used when checking object permissions.

        See: icms/web/auth/backends.py
        """

        self.guardian_checker = ObjectPermissionChecker(self)

    REQUIRED_FIELDS = [
        "email",
        "first_name",
        "last_name",
        "date_of_birth",
    ]

    title = models.CharField(max_length=20, blank=True, null=True)
    organisation = models.CharField(max_length=4000, blank=True, null=True)
    department = models.CharField(max_length=4000, blank=True, null=True)
    job_title = models.CharField(max_length=320, blank=True, null=True)
    location_at_address = models.CharField(max_length=4000, blank=True, null=True)
    work_address = models.CharField(max_length=300, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return " ".join(filter(None, (self.title, self.first_name, self.last_name)))

    @property
    def account_last_login_date(self):
        return None if self.last_login is None else self.last_login.date()

    class Meta:
        ordering = ("-is_active", "first_name")


class PhoneNumber(models.Model):
    WORK = "WORK"
    FAX = "FAX"
    MOBILE = "MOBILE"
    HOME = "HOME"
    MINICOM = "MINICOM"
    TYPES = ((WORK, "Work"), (FAX, "Fax"), (MOBILE, "Mobile"), (HOME, "Home"), (MINICOM, "Minicom"))
    phone = models.CharField(max_length=60, blank=False, null=False)
    type = models.CharField(max_length=30, choices=TYPES, blank=False, null=False, default=WORK)
    comment = models.CharField(max_length=4000, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="phone_numbers"
    )

    @property
    def entity_type(self):
        return dict(PhoneNumber.TYPES)[self.type]


class Email(models.Model):
    WORK = "WORK"
    HOME = "HOME"
    TYPES = ((WORK, "Work"), (HOME, "Home"))
    email = models.EmailField(max_length=254, blank=False, null=False)
    type = models.CharField(max_length=30, choices=TYPES, blank=False, null=False, default=WORK)
    portal_notifications = models.BooleanField(blank=False, null=False, default=False)
    comment = models.CharField(max_length=4000, blank=True, null=True)
    is_primary = models.BooleanField(blank=False, null=False, default=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emails"
    )

    def __str__(self):
        return self.email
