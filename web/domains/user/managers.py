from django.contrib.auth.models import UserManager as BaseUserManager


# TODO: Revisit in ICMSLST-2047 to remove this completely
class UserManager(BaseUserManager):
    """Custom user model manager to handle extra fields"""

    def create_user(self, username, password=None, **extra_fields):
        # TODO: Revisit in ICMSLST-2047 (defaults to true in model anyway)
        extra_fields.setdefault("is_active", True)

        # TODO: Revisit in ICMSLST-2047 (We want to use standard django auth)
        # Users migrating from V1 will have to reset their password (so remove).
        extra_fields.setdefault("password_disposition", "TEMPORARY")

        # TODO: Revisit in ICMSLST-2047 Investigate missing email field
        return super().create_user(username, password=password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        """Create and save a SuperUser with given info"""

        # TODO: Revisit in ICMSLST-2047 (defaults to true in model anyway)
        extra_fields.setdefault("is_active", True)

        # Users migrating from V1 will have to reset their password (so remove).
        extra_fields.setdefault("password_disposition", "FULL")

        # TODO: Revisit in ICMSLST-2047 Investigate missing email field
        return super().create_superuser(username, password=password, **extra_fields)
