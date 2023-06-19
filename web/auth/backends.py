from django.contrib.auth.backends import ModelBackend
from guardian.backends import check_support
from guardian.conf import settings as guardian_settings
from guardian.ctypes import get_content_type
from guardian.exceptions import WrongAppError

from web.models import User


class ModelAndObjectPermissionBackend(ModelBackend):
    """Custom django authentication backend.

    Combination of django.contrib.auth.backends and guardian.backends.ObjectPermissionBackend.
    """

    def has_perm(self, user_obj, perm, obj=None):
        """Return True if given user_obj has permission for obj.

        If obj is None ModelBackend.has_perm is used.
        if obj is supplied user_obj.guardian_checker is used.
        All object permission checking code is taken directly from ObjectPermissionBackend.has_perm
        """

        # Default to ModelBackend.has_perm when obj is None
        if obj is None:
            return super().has_perm(user_obj, perm, obj)

        #
        # Code from ObjectPermissionBackend.has_perm
        #

        # check if user_obj and object are supported
        support, user_obj = check_support(user_obj, obj)
        if not support:
            return False

        if "." in perm:
            app_label, _ = perm.split(".", 1)
            if app_label != obj._meta.app_label:
                # Check the content_type app_label when permission
                # and obj app labels don't match.
                ctype = get_content_type(obj)
                if app_label != ctype.app_label:
                    raise WrongAppError(
                        "Passed perm has app label of '%s' while "
                        "given obj has app label '%s' and given obj"
                        "content_type has app label '%s'"
                        % (app_label, obj._meta.app_label, ctype.app_label)
                    )

        if not user_obj.guardian_checker:
            user_obj.set_guardian_checker()

        check = user_obj.guardian_checker
        return check.has_perm(perm, obj)

    def get_all_permissions(self, user_obj, obj=None):
        """Return set of permission strings for the given user_obj.

        If obj is None ModelBackend.get_all_permissions is used.
        if obj is supplied user_obj.guardian_checker is used.
        All object permission checking code is taken directly from ObjectPermissionBackend.get_all_permissions
        """

        # Default to ModelBackend.get_all_permissions when obj is None
        if not obj:
            return super().get_all_permissions(user_obj, obj)

        #
        # Code from ObjectPermissionBackend.get_all_permissions
        #

        # check if user_obj and object are supported
        support, user_obj = check_support(user_obj, obj)
        if not support:
            return set()

        if not user_obj.guardian_checker:
            user_obj.set_guardian_checker()

        check = user_obj.guardian_checker
        return check.get_perms(obj)

    def get_user_permissions(self, user_obj, obj=None):
        """Only user group permissions are used when checking for global permissions."""

        return set()


def get_anonymous_user_instance(user_model: type[User]) -> User:
    # Change the guardian anonymous user pk to match V1 guest user
    kwargs = {
        "pk": 0,
        user_model.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME,
    }
    user = user_model(**kwargs)
    user.set_unusable_password()

    return user
