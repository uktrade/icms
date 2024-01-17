from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, RedirectView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from web.errors import APIError
from web.forms import utils
from web.models import Email, PhoneNumber, User
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.postcode import api_postcode_to_address_lookup
from web.utils.sentry import capture_exception
from web.views import ModelFilterView

from . import actions
from .forms import (
    ManualAddressEntryForm,
    PostCodeSearchForm,
    UserDetailsUpdateForm,
    UserEmailForm,
    UserListFilter,
    UserPhoneNumberForm,
)
from .formset import new_emails_formset, new_user_phones_formset


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


@login_required
def current_user_details(request: AuthenticatedHttpRequest) -> HttpResponse:
    return _get_user_details(request, request.user.pk)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def user_details(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    return _get_user_details(request, pk)


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


def _get_user_details(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    """Helper function to return user details."""

    action = request.POST.get("action")
    if action == "edit_address":
        # Save all data to session before searching address
        # to restore from session after address search is complete
        request.session["user_details"] = request.POST
    if action in ["search_address", "edit_address"]:
        return _address_search(request, action)
    elif action in ["manual_address", "save_manual_address"]:
        return _manual_address(request, action, pk)

    return _details_update(request, action, pk)


def _address_search(request: AuthenticatedHttpRequest, action: str) -> HttpResponse:
    if action == "edit_address":  # Initial request
        postcode_form = PostCodeSearchForm()
    else:
        postcode_form = PostCodeSearchForm(request.POST)

    addresses = []
    if postcode_form.is_valid():
        try:
            addresses = api_postcode_to_address_lookup(postcode_form.cleaned_data.get("post_code"))

        except APIError as e:
            # don't bother logging sentries when users type in invalid postcodes
            if e.status_code not in (400, 404):
                capture_exception()

            messages.warning(request, e.error_msg)

        except Exception:
            capture_exception()

            messages.warning(request, "Unable to lookup postcode")

    return render(
        request,
        "web/domains/user/search-address.html",
        {"postcode_form": postcode_form, "addresses": addresses},
    )


def _manual_address(request: AuthenticatedHttpRequest, action: str, pk: int) -> HttpResponse:
    form = ManualAddressEntryForm(request.POST or None)

    if form.is_valid():
        if action == "save_manual_address":
            return _details_update(request, "save_address", pk)

    return render(request, "web/domains/user/manual-address.html", {"form": form})


def _details_update(request: AuthenticatedHttpRequest, action: str, pk: int) -> HttpResponse:
    forms = _init_user_details_forms(request, action, pk)
    if not action == "save_address":
        if utils.forms_valid(forms):
            utils.save_forms(forms)
            # Create fresh forms  to remove objects before sending response
            forms["phones_formset"] = new_user_phones_formset(request)
            forms["emails_formset"] = new_emails_formset(request)
            messages.success(request, "Central contact details have been saved.")

            return redirect(request.build_absolute_uri())

        else:
            if request.method == "POST":
                messages.error(request, "Please correct the highlighted errors.")

    is_user = request.user.pk == pk
    # Only show account recovery for user accounts that haven't come from V1.
    show_account_recovery = is_user and not request.user.icms_v1_user

    context = forms | {
        "show_account_recovery": show_account_recovery,
        "show_password_change": (
            is_user and not settings.STAFF_SSO_ENABLED and not settings.GOV_UK_ONE_LOGIN_ENABLED
        ),
    }

    return render(
        request,
        "web/domains/user/details.html"
        if request.user.pk == pk
        else "web/domains/user/admin-view-details.html",
        context,
    )


def _init_user_details_forms(
    request: AuthenticatedHttpRequest, action: str, pk: int
) -> dict[str, Any]:
    # If post is not made from user details page but from search page do not
    # try and initialise forms with POST data
    data = request.POST or None
    user = User.objects.get(pk=pk)
    address = None

    if request.method == "POST":
        if action == "save_address":
            address = request.POST.get("address")
            data = request.session.pop("user_details")

    details_data = data and data.copy() or None
    if address and details_data:
        details_data["work_address"] = address

    details_form = UserDetailsUpdateForm(details_data, instance=user)
    phones_formset = new_user_phones_formset(request, data=data)
    emails_formset = new_emails_formset(request, data=data)

    # get details form data from session if exists and not the first page load
    all_forms = {
        "details_form": details_form,
        "phones_formset": phones_formset,
        "emails_formset": emails_formset,
    }

    return all_forms
