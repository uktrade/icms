from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from web.domains.contacts.forms import ContactForm
from web.permissions import (
    Perms,
    constabulary_add_contact,
    constabulary_get_contacts,
    constabulary_remove_contact,
)
from web.types import AuthenticatedHttpRequest
from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, Edit, Unarchive

from .forms import ConstabulariesFilter, ConstabularyForm
from .models import Constabulary


class ConstabularyListView(ModelFilterView):
    template_name = "web/domains/constabulary/list.html"
    model = Constabulary
    filterset_class = ConstabulariesFilter
    permission_required = Perms.sys.ilb_admin
    page_title = "Maintain Constabularies"

    class Display:
        fields = ["name", "region_verbose", "email", "telephone_number"]
        fields_config = {
            "name": {"header": "Constabulary Name", "link": True},
            "region_verbose": {"header": "Constabulary Region"},
            "email": {"header": "Email Address"},
            "telephone_number": {"header": "Telephone Number"},
        }
        actions = [Archive(), Unarchive(), Edit(hide_if_archived_object=True)]


class ConstabularyCreateView(ModelCreateView):
    template_name = "web/domains/constabulary/add.html"
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy("constabulary:list")
    cancel_url = success_url
    permission_required = Perms.sys.ilb_admin
    page_title = "New Constabulary"


class ConstabularyEditView(ModelUpdateView):
    template_name = "web/domains/constabulary/edit.html"
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy("constabulary:list")
    cancel_url = success_url
    permission_required = Perms.sys.ilb_admin

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        contacts = constabulary_get_contacts(self.object)

        return context | {
            "contacts": contacts,
            "object_permissions": [
                (
                    Perms.obj.constabulary.verified_fa_authority_editor,
                    "Verified Firearms Authority Editor",
                ),
            ],
            "contact_form": ContactForm(contacts_to_exclude=contacts),
        }


class ConstabularyDetailView(ModelDetailView):
    template_name = "web/domains/constabulary/view.html"
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy("constabulary:list")
    cancel_url = success_url
    permission_required = Perms.sys.ilb_admin

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        contacts = constabulary_get_contacts(self.object)

        return context | {
            "contacts": contacts,
            "object_permissions": [
                (
                    Perms.obj.constabulary.verified_fa_authority_editor,
                    "Verified Firearms Authority Editor",
                ),
            ],
        }


class ConstabularyContactsBaseView(
    PermissionRequiredMixin, LoginRequiredMixin, SingleObjectMixin, View
):
    # View config
    http_method_names = ["post"]

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.ilb_admin]

    # SingleObjectMixin config
    model = Constabulary

    def get_success_url(self) -> str:
        pk = self.kwargs.get(self.pk_url_kwarg)
        return reverse("constabulary:edit", kwargs={"pk": pk})


class AddConstabularyContactView(ConstabularyContactsBaseView):
    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        constabulary = self.get_object()

        contacts = constabulary_get_contacts(constabulary)
        form = ContactForm(request.POST, contacts_to_exclude=contacts)

        if form.is_valid():
            contact = form.cleaned_data["contact"]

            with transaction.atomic():
                constabulary_add_contact(constabulary, contact)

        else:
            messages.error(request, "Unable to add contact.")

        return redirect(self.get_success_url())


class DeleteConstabularyContactView(ConstabularyContactsBaseView):
    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        constabulary = self.get_object()

        contacts = constabulary_get_contacts(constabulary)
        contact = get_object_or_404(contacts, pk=self.kwargs["contact_pk"])

        with transaction.atomic():
            constabulary_remove_contact(constabulary, contact)

        return redirect(self.get_success_url())
