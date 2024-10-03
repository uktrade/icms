from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from web.mail.emails import send_org_contact_invite_email
from web.models import (
    Exporter,
    ExporterContactInvite,
    Importer,
    ImporterContactInvite,
    User,
)
from web.permissions import (
    can_user_manage_org_contacts,
    is_user_org_admin,
    organisation_add_contact,
    organisation_get_contacts,
    organisation_remove_contact,
)
from web.types import AuthenticatedHttpRequest

from .forms import AcceptOrgInviteForm, ContactForm, InviteOrgContactForm

Org = Importer | Exporter
OrgT = type[Org]


def _get_class_imp_or_exp(org_type: str) -> OrgT:
    if org_type == "importer":
        return Importer
    elif org_type == "exporter":
        return Exporter
    else:
        raise NotImplementedError(f"Unknown case_type {org_type}")


@login_required
@require_POST
def add(request: AuthenticatedHttpRequest, *, org_type: str, org_pk: int) -> HttpResponse:
    """View used by org admins to add importer / exporter contacts"""
    model_class = _get_class_imp_or_exp(org_type)
    org: Org = get_object_or_404(model_class, pk=org_pk)

    if not is_user_org_admin(request.user, org):
        raise PermissionDenied

    with transaction.atomic():
        contacts = organisation_get_contacts(org)
        form = ContactForm(request.POST, contacts_to_exclude=contacts)

        if form.is_valid():
            contact = form.cleaned_data["contact"]
            organisation_add_contact(org, contact)

        else:
            messages.error(request, "Unable to add contact.")

    parent_url = get_parent_url(org, org_type)

    return redirect(parent_url)


@login_required
@require_POST
def delete(
    request: AuthenticatedHttpRequest, *, org_type: str, org_pk: int, contact_pk: int
) -> HttpResponse:
    """View used by org admins to remove importer / exporter contacts"""

    model_class = _get_class_imp_or_exp(org_type)
    org: Org = get_object_or_404(model_class, pk=org_pk)

    if not is_user_org_admin(request.user, org):
        raise PermissionDenied

    contacts = organisation_get_contacts(org)

    with transaction.atomic():
        contact = get_object_or_404(contacts, pk=contact_pk)

        organisation_remove_contact(org, contact)

    parent_url = get_parent_url(org, org_type)

    return redirect(parent_url)


class InviteOrgContactView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    # FormView config
    form_class = InviteOrgContactForm
    template_name = "web/domains/organisation/invite-contact.html"

    def has_permission(self):
        return can_user_manage_org_contacts(self.request.user, self._get_org())

    def get_success_url(self):
        org_type = self.kwargs["org_type"]
        org = self._get_org()

        return get_parent_url(org, org_type)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        org_label = self.kwargs["org_type"].title()

        context["page_title"] = f"Invite an {org_label} Contact"
        context["organisation"] = org_label
        context["parent_url"] = self.get_success_url()

        return context

    def form_valid(self, form: InviteOrgContactForm) -> HttpResponseRedirect:
        organisation = self._get_org()
        invite_email = form.cleaned_data["email"]
        invite_first_name = form.cleaned_data["first_name"]
        invite_last_name = form.cleaned_data["last_name"]

        # Check for existing ICMS users who are contacts already
        existing_user = User.objects.filter(email=invite_email).first()
        if existing_user and existing_user in organisation_get_contacts(organisation):
            messages.warning(self.request, "User with that email is already a contact.")

            return super().form_invalid(form)

        # Get or create the invite (if one already exists)
        invite_cls = self._get_invite()
        invite, created = invite_cls.objects.get_or_create(
            organisation=organisation,
            email=invite_email,
            processed=False,
            defaults={
                "invited_by": self.request.user,
                "first_name": invite_first_name,
                "last_name": invite_last_name,
            },
        )

        # For an existing unprocessed invite update the defaults from the earlier invite
        # Assuming they may have been wrong the first time
        if not created:
            invite.invited_by = self.request.user
            invite.first_name = invite_first_name
            invite.last_name = invite_last_name
            invite.save()

        # Send out invite
        send_org_contact_invite_email(organisation, invite)

        # Add success message
        messages.success(self.request, "Sent invite to contact.")

        return super().form_valid(form)

    def _get_org(self) -> Org:
        org_type = self.kwargs["org_type"]
        org_pk = self.kwargs["org_pk"]

        model_class = _get_class_imp_or_exp(org_type)
        org: Org = get_object_or_404(model_class, pk=org_pk)

        return org

    def _get_invite(self) -> type[ExporterContactInvite | ImporterContactInvite]:
        org_type = self.kwargs["org_type"]
        if org_type == "importer":
            return ImporterContactInvite
        elif org_type == "exporter":
            return ExporterContactInvite
        else:
            raise NotImplementedError(f"Unknown case_type {org_type}")


class AcceptOrgContactInviteView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    # FormView config
    form_class = AcceptOrgInviteForm
    template_name = "web/domains/organisation/accept-org-invite.html"

    def test_func(self):
        """Check the invite exists for the logged-in user."""
        # Only match invites linked to the user.
        kwargs = {
            "email": self.request.user.email,
            "code": self.kwargs["code"],
            "processed": False,
        }

        importer_invite = ImporterContactInvite.objects.filter(**kwargs)
        exporter_invite = ExporterContactInvite.objects.filter(**kwargs)

        return importer_invite.exists() or exporter_invite.exists()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        invite = self._get_invite()

        context["invited_by"] = invite.invited_by.full_name

        # importer display_name or name (common to exporter and importer)
        context["organisation_name"] = getattr(
            invite.organisation, "display_name", invite.organisation.name
        )

        return context

    def form_valid(self, form: AcceptOrgInviteForm) -> HttpResponseRedirect:
        invite = self._get_invite()

        if form.cleaned_data["accept_invite"]:
            organisation_add_contact(invite.organisation, self.request.user)

        invite.processed = True
        invite.save()

        return super().form_valid(form)

    def _get_invite(self) -> ExporterContactInvite | ImporterContactInvite:
        # Only match invites linked to the user.
        importer_invites = ImporterContactInvite.objects.filter(
            email=self.request.user.email, code=self.kwargs["code"], processed=False
        )

        if importer_invites.exists():
            return importer_invites.get()

        exporter_invites = ExporterContactInvite.objects.filter(
            email=self.request.user.email, code=self.kwargs["code"], processed=False
        )

        if exporter_invites.exists():
            return exporter_invites.get()

        raise PermissionDenied

    def get_success_url(self):
        return reverse("workbasket")


def get_parent_url(org: Org, org_type: str) -> str:
    if org.is_agent():
        return reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk})
    else:
        return reverse(f"{org_type}-edit", kwargs={"pk": org.pk})
