from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from web.errors import APIError
from web.forms import utils
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.postcode import api_postcode_to_address_lookup
from web.utils.sentry import capture_exception
from web.views import ModelFilterView

from . import actions
from .forms import (
    ManualAddressEntryForm,
    PeopleFilter,
    PostCodeSearchForm,
    UserDetailsUpdateForm,
    UserListFilter,
)
from .formset import (
    new_alternative_emails_formset,
    new_personal_emails_formset,
    new_user_phones_formset,
)
from .models import User


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


class PeopleSearchView(ModelFilterView):
    template_name = "web/domains/user/search-people.html"
    filterset_class = PeopleFilter
    model = User
    permission_required: list[str] = []
    page_title = "Search People"

    def get_page(self):
        return self.request.POST.get("page")

    def get_filterset(self, **kwargs):
        return self.filterset_class(
            self.request.POST or None, queryset=self.get_queryset(), **kwargs
        )

    class Display:
        fields = [("title", "first_name", "last_name"), ("organisation", "email"), "work_address"]
        fields_config = {
            "title": {"header": "Name"},
            "first_name": {"no_header": True},
            "last_name": {"no_header": True},
            "organisation": {"header": "Job Details"},
            "email": {"no_header": True},
            "work_address": {"header": "Organisation Address"},
        }
        select = True


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
            forms["alternative_emails_formset"] = new_alternative_emails_formset(request)
            forms["personal_emails_formset"] = new_personal_emails_formset(request)
            messages.success(request, "Central contact details have been saved.")

            return redirect(request.build_absolute_uri())

        else:
            if request.method == "POST":
                messages.error(request, "Please correct the highlighted errors.")

    return render(
        request,
        "web/domains/user/details.html"
        if request.user.pk == pk
        else "web/domains/user/admin-view-details.html",
        forms,
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
    alternative_emails_formset = new_alternative_emails_formset(request, data=data)
    personal_emails_formset = new_personal_emails_formset(request, data=data)

    # get details form data from session if exists and not the first page load
    all_forms = {
        "details_form": details_form,
        "phones_formset": phones_formset,
        "alternative_emails_formset": alternative_emails_formset,
        "personal_emails_formset": personal_emails_formset,
    }

    return all_forms
