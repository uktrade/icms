from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.urls import reverse
from django.views.generic import CreateView, DetailView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from web.models import Email, PhoneNumber, User
from web.permissions import Perms
from web.views import ModelFilterView

from . import actions
from .forms import (
    UserDetailsUpdateForm,
    UserEmailForm,
    UserListFilter,
    UserPhoneNumberForm,
)


class UserBaseMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin used in all user views that modify data relating to the request user.

    Defines authentication requirements and common context.
    """

    def test_func(self):
        return self.kwargs["user_pk"] == self.request.user.pk

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | {
            "show_password_change": (
                not settings.STAFF_SSO_ENABLED and not settings.GOV_UK_ONE_LOGIN_ENABLED
            ),
            # Only show account recovery for user accounts that haven't come from V1.
            "show_account_recovery": not self.request.user.icms_v1_user,
        }

    def get_success_url(self):
        """Used in create and update views."""
        return reverse("user-edit", kwargs={"user_pk": self.request.user.pk})

    def get_redirect_url(self, *args, **kwargs):
        """Used in delete views."""
        return reverse("user-edit", kwargs={"user_pk": self.request.user.pk})


class UserUpdateView(UserBaseMixin, UpdateView):
    model = User
    pk_url_kwarg = "user_pk"
    form_class = UserDetailsUpdateForm
    template_name = "web/domains/user/user_edit.html"


class UserCreateTelephoneView(UserBaseMixin, CreateView):
    model = PhoneNumber
    form_class = UserPhoneNumberForm
    extra_context = {"sub_title": "Add Phone Number"}
    template_name = "web/domains/user/user_add_related.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.user = self.request.user

        return form


class UserUpdateTelephoneView(UserBaseMixin, UpdateView):
    model = PhoneNumber
    pk_url_kwarg = "phonenumber_pk"
    form_class = UserPhoneNumberForm
    extra_context = {"sub_title": "Edit Phone Number"}
    template_name = "web/domains/user/user_edit_related.html"


class UserDeleteTelephoneView(UserBaseMixin, SingleObjectMixin, RedirectView):
    http_method_names = ["post"]
    model = PhoneNumber
    pk_url_kwarg = "phonenumber_pk"

    def post(self, request, *args, **kwargs):
        phone_number = self.get_object()
        phone_number.delete()

        return super().post(request, *args, **kwargs)


class UserCreateEmailView(UserBaseMixin, CreateView):
    model = Email
    form_class = UserEmailForm
    extra_context = {"sub_title": "Add Email Address"}
    template_name = "web/domains/user/user_add_related.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.user = self.request.user

        return form


class UserUpdateEmailView(UserBaseMixin, UpdateView):
    model = Email
    pk_url_kwarg = "email_pk"
    form_class = UserEmailForm
    extra_context = {"sub_title": "Edit Email Address"}
    template_name = "web/domains/user/user_edit_related.html"


class UserDeleteEmailView(UserBaseMixin, SingleObjectMixin, RedirectView):
    http_method_names = ["post"]
    model = Email
    pk_url_kwarg = "email_pk"

    def post(self, request, *args, **kwargs):
        email = self.get_object()

        if email.is_primary:
            messages.warning(
                request,
                "Unable to delete Primary email address. Please set another email address as primary before deleting.",
            )
        elif email.email.casefold() == self.request.user.email.casefold():
            messages.warning(request, "Unable to delete email address used for account login.")
        else:
            email.delete()

        return super().post(request, *args, **kwargs)


class UsersListView(ModelFilterView):
    template_name = "web/domains/user/list.html"
    model = User
    filterset_class = UserListFilter
    page_title = "Maintain Web User Accounts"
    permission_required = Perms.sys.ilb_admin

    class Display:
        fields = [
            "full_name",
            ("organisation", "job_title"),
            "username",
            "account_last_login_date",
        ]
        fields_config = {
            "full_name": {"header": "Person Details", "link": True},
            "organisation": {"header": "Organisation"},
            "job_title": {"header": "Job Title"},
            "username": {"header": "Login Name"},
            "account_last_login_date": {"header": "Last Login Date"},
        }
        actions = [actions.DeactivateUser(), actions.ActivateUser()]
        select = True


class UserDetailView(PermissionRequiredMixin, DetailView):
    # PermissionRequiredMixin config
    permission_required = Perms.sys.ilb_admin

    # DetailView config
    model = User
    pk_url_kwarg = "user_pk"
    context_object_name = "user"
    http_method_names = ["get"]
    template_name = "web/domains/user/detail.html"
