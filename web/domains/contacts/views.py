from typing import Union

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from web.models import Exporter, Importer
from web.permissions import (
    Perms,
    organisation_add_contact,
    organisation_get_contacts,
    organisation_remove_contact,
)
from web.types import AuthenticatedHttpRequest

from .forms import ContactForm

Org = Union[Importer, Exporter]
OrgT = type[Org]


def _get_class_imp_or_exp(org_type: str) -> OrgT:
    if org_type == "importer":
        return Importer
    elif org_type == "exporter":
        return Exporter
    else:
        raise NotImplementedError(f"Unknown case_type {org_type}")


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def add(request: AuthenticatedHttpRequest, *, org_type: str, org_pk: int):
    """Add a contact to an importer / exporter"""

    model_class = _get_class_imp_or_exp(org_type)
    org: Org = get_object_or_404(model_class, pk=org_pk)

    contacts = organisation_get_contacts(org)
    form = ContactForm(request.POST, contacts_to_exclude=contacts)

    if form.is_valid():
        contact = form.cleaned_data["contact"]
        organisation_add_contact(org, contact)

    else:
        messages.error(request, "Unable to add contact.")

    if org.is_agent():
        return redirect(reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk}))

    else:
        return redirect(reverse(f"{org_type}-edit", kwargs={"pk": org.pk}))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
@require_POST
def delete(request: AuthenticatedHttpRequest, *, org_type: str, org_pk: int, contact_pk: int):
    model_class = _get_class_imp_or_exp(org_type)
    org: Org = get_object_or_404(model_class, pk=org_pk)

    contacts = organisation_get_contacts(org)
    contact = get_object_or_404(contacts, pk=contact_pk)

    organisation_remove_contact(org, contact)

    if org.is_agent():
        return redirect(reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk}))

    else:
        return redirect(reverse(f"{org_type}-edit", kwargs={"pk": org.pk}))
