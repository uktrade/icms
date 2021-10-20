from typing import TYPE_CHECKING, Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from guardian.shortcuts import assign_perm, get_users_with_perms, remove_perm

from web.domains.user.models import User
from web.models import Exporter, Importer
from web.types import AuthenticatedHttpRequest

from .forms import ContactForm

if TYPE_CHECKING:
    from django.db.models import QuerySet

Org = Union[Importer, Exporter]
OrgT = Type[Org]


def _get_class_imp_or_exp(org_type: str) -> OrgT:
    if org_type == "importer":
        return Importer
    elif org_type == "exporter":
        return Exporter
    else:
        raise NotImplementedError(f"Unknown case_type {org_type}")


# TODO: ICMSLST-859 ICMSLST-860 org's contacts can view/edit org details
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def add(request: AuthenticatedHttpRequest, *, org_type: str, org_pk: int):
    model_class = _get_class_imp_or_exp(org_type)
    org: Org = get_object_or_404(model_class, pk=org_pk)

    contacts: "QuerySet[User]" = current_contacts(org)

    form = ContactForm(request.POST, contacts_to_exclude=contacts)
    if form.is_valid():
        contact = form.cleaned_data["contact"]
        assign_contact_perm(org, contact)

    if org.is_agent():
        return redirect(reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk}))

    else:
        return redirect(reverse(f"{org_type}-edit", kwargs={"pk": org.pk}))


# TODO: ICMSLST-859 ICMSLST-860 org's contacts can view/edit org details
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def delete(request: AuthenticatedHttpRequest, *, org_type: str, org_pk: int, contact_pk: int):
    model_class = _get_class_imp_or_exp(org_type)
    org: Org = get_object_or_404(model_class, pk=org_pk)

    contacts: "QuerySet[User]" = current_contacts(org)
    contact = get_object_or_404(contacts, pk=contact_pk)

    delete_contact_perm(org, contact)

    if org.is_agent():
        return redirect(reverse(f"{org_type}-agent-edit", kwargs={"pk": org.pk}))

    else:
        return redirect(reverse(f"{org_type}-edit", kwargs={"pk": org.pk}))


def current_contacts(org: Org) -> "QuerySet[User]":
    """Current active contacts associated with importer/exporter/agent."""
    if isinstance(org, Importer):
        return get_users_with_perms(org, only_with_perms_in=["is_contact_of_importer"]).filter(
            user_permissions__codename="importer_access"
        )

    elif isinstance(org, Exporter):
        return get_users_with_perms(org, only_with_perms_in=["is_contact_of_exporter"]).filter(
            user_permissions__codename="exporter_access"
        )

    else:
        raise NotImplementedError(f"Unknown org {org}")


def assign_contact_perm(org: Org, contact: User) -> None:
    if isinstance(org, Importer):
        permission = Permission.objects.get(codename="importer_access")
        contact.user_permissions.add(permission)

        if org.is_agent():

            assign_perm("web.is_agent_of_importer", contact, org.main_importer)
            assign_perm("web.is_contact_of_importer", contact, org)
        else:
            assign_perm("web.is_contact_of_importer", contact, org)

    elif isinstance(org, Exporter):
        permission = Permission.objects.get(codename="exporter_access")
        contact.user_permissions.add(permission)

        if org.is_agent():
            assign_perm("web.is_agent_of_exporter", contact, org.main_exporter)
            assign_perm("web.is_contact_of_exporter", contact, org)
        else:
            assign_perm("web.is_contact_of_exporter", contact, org)

    else:
        raise NotImplementedError(f"Unknown org {org}")


def delete_contact_perm(org: Org, contact: User) -> None:
    if isinstance(org, Importer):
        if org.is_agent():
            remove_perm("web.is_agent_of_importer", contact, org.main_importer)
            remove_perm("web.is_contact_of_importer", contact, org)
        else:
            remove_perm("web.is_contact_of_importer", contact, org)

    elif isinstance(org, Exporter):
        if org.is_agent():
            remove_perm("web.is_agent_of_exporter", contact, org.main_exporter)
            remove_perm("web.is_contact_of_exporter", contact, org)
        else:
            remove_perm("web.is_contact_of_exporter", contact, org)

    else:
        raise NotImplementedError(f"Unknown org {org}")
