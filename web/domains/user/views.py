from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.db import transaction
from django.db.models import QuerySet
from django.forms import Form
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    RedirectView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from web.auth.backends import ANONYMOUS_USER_PK
from web.domains.template.context import UserManagementContext
from web.domains.template.utils import replace_template_values
from web.mail.constants import EmailTypes
from web.mail.emails import send_case_email
from web.middleware.one_login import new_one_login_user
from web.models import CaseEmail, Email, PhoneNumber, Template, User
from web.permissions import Perms
from web.sites import is_exporter_site, is_importer_site
from web.types import AuthenticatedHttpRequest
from web.views import ModelFilterView

from .actions import ActivateUser, DeactivateUser
from .forms import (
    UserDetailsUpdateForm,
    UserEmailForm,
    UserListFilter,
    UserManagementEmailForm,
    UserPhoneNumberForm,
)


def user_list_view_qs() -> QuerySet[User]:
    """Reusable QuerySet that can be used in several views."""
    return User.objects.exclude(pk=ANONYMOUS_USER_PK).exclude(is_superuser=True)


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
    new_one_login_user = False

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> Any:
        user = self.request.user
        self.new_one_login_user = new_one_login_user(user)

        return super().post(request, *args, **kwargs)

    def get_success_url(self) -> str:
        # Redirect to new access request page when user updates their details correctly.
        if self.new_one_login_user:
            self.request.user.refresh_from_db()
            user = self.request.user
            site = self.request.site

            if not new_one_login_user(user):
                if is_exporter_site(site):
                    return reverse("access:exporter-request")
                elif is_importer_site(site):
                    return reverse("access:importer-request")

        return super().get_success_url()


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

    def get_queryset(self) -> QuerySet[User]:
        return user_list_view_qs().exclude(pk=self.request.user.pk)

    class Display:
        actions = [DeactivateUser(), ActivateUser()]
        fields = [
            "full_name",
            ("organisation", "job_title"),
            "username",
            "is_active",
            "account_last_login_date",
        ]
        fields_config = {
            "full_name": {"header": "Person Details", "link": True},
            "organisation": {"header": "Organisation"},
            "job_title": {"header": "Job Title"},
            "username": {"header": "Login Name"},
            "is_active": {"header": "Is Active"},
            "account_last_login_date": {"header": "Last Login Date"},
        }
        select = True


class UserDetailView(PermissionRequiredMixin, DetailView):
    # PermissionRequiredMixin config
    permission_required = Perms.sys.ilb_admin

    # DetailView config
    template_name = "web/domains/user/detail.html"
    pk_url_kwarg = "user_pk"
    context_object_name = "platform_user"
    http_method_names = ["get"]
    queryset = user_list_view_qs()


@method_decorator(transaction.atomic, name="post")
class UserReactivateFormView(PermissionRequiredMixin, FormView):
    permission_required = Perms.sys.ilb_admin
    template_name = "web/domains/user/user_management.html"
    form_class = UserManagementEmailForm
    email_template_code = EmailTypes.REACTIVATE_USER_EMAIL

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        platform_user = self.get_platform_user()
        return context | {
            "page_title": f"Reactivate {platform_user.full_name}'s account",
            "platform_user": platform_user,
            "action": "Reactivate user",
        }

    def get_platform_user(self) -> User:
        return user_list_view_qs().exclude(pk=self.request.user.pk).get(pk=self.kwargs["user_pk"])

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        user = self.get_platform_user()
        ctx = UserManagementContext(user)
        email_template = Template.objects.get(template_code=self.email_template_code)
        return initial | {
            "subject": replace_template_values(email_template.template_name, ctx),
            "body": replace_template_values(email_template.template_content, ctx),
        }

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        response = super().form_valid(form)
        user: User = self.get_platform_user()
        self.update_user(user)
        message = "User successfully updated"
        if form.cleaned_data["send_email"]:
            case_email = CaseEmail.objects.create(
                to=user.email,
                template_code=self.email_template_code,
                subject=form.cleaned_data["subject"],
                body=form.cleaned_data["body"],
            )
            send_case_email(case_email)
            message = f"{message} & email sent"

        messages.info(self.request, message)
        return response

    def update_user(self, user: User) -> None:
        user.is_active = True
        user.save()

    def get_success_url(self) -> str:
        return reverse("users-list") + f"?email_address={self.get_platform_user().email}"


@method_decorator(transaction.atomic, name="post")
class UserDeactivateFormView(UserReactivateFormView):
    permission_required = Perms.sys.ilb_admin
    email_template_code = EmailTypes.DEACTIVATE_USER_EMAIL

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        platform_user = self.get_platform_user()
        return context | {
            "page_title": f"Deactivate {platform_user.full_name}'s account",
            "action": "Deactivate user",
            "platform_user": platform_user,
        }

    def update_user(self, user: User) -> None:
        user.is_active = False
        user.save()
