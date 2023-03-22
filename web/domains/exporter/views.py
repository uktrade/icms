from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from web.domains.contacts.forms import ContactForm
from web.domains.exporter.forms import AgentForm, ExporterFilter, ExporterForm
from web.domains.office.forms import ExporterOfficeForm
from web.permissions import ExporterObjectPermissions, Perms, get_organisation_contacts
from web.types import AuthenticatedHttpRequest
from web.views import ModelFilterView
from web.views.actions import Archive, CreateExporterAgent, Edit, Unarchive

from .models import Exporter


class ExporterListView(ModelFilterView):
    template_name = "web/domains/exporter/list.html"
    filterset_class = ExporterFilter
    model = Exporter
    permission_required = "web.ilb_admin"
    page_title = "Maintain Exporters"

    class Display:
        fields = ["name", "offices", "agents"]
        fields_config = {
            "name": {"header": "Exporter Name", "link": True},
            "offices": {
                "header": "Addresses",
                "show_all": True,
                "query_filter": {"is_active": True},
            },
            "agents": {"header": "Agent", "show_all": True, "query_filter": {"is_active": True}},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [Edit(**opts), CreateExporterAgent(**opts), Archive(**opts), Unarchive(**opts)]


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_exporter(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    exporter: Exporter = get_object_or_404(Exporter, pk=pk)

    if request.method == "POST":
        form = ExporterForm(request.POST, instance=exporter)
        if form.is_valid():
            form.save()
            return redirect(reverse("exporter-edit", kwargs={"pk": pk}))
    else:
        form = ExporterForm(instance=exporter)

    contacts = get_organisation_contacts(exporter)
    object_permissions = get_exporter_object_permissions()

    context = {
        "object": exporter,
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "object_permissions": object_permissions,
        "org_type": "exporter",
    }

    return render(request, "web/domains/exporter/edit.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def detail_exporter(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    exporter: Exporter = get_object_or_404(Exporter, pk=pk)

    contacts = get_organisation_contacts(exporter)
    object_permissions = get_exporter_object_permissions()

    context = {
        "object": exporter,
        "contacts": contacts,
        "object_permissions": object_permissions,
        "org_type": "exporter",
    }

    return render(request, "web/domains/exporter/detail.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_exporter(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ExporterForm(request.POST)
        if form.is_valid():
            exporter: Exporter = form.save()

            return redirect(reverse("exporter-edit", kwargs={"pk": exporter.pk}))
    else:
        form = ExporterForm()

    return render(request, "web/domains/exporter/create.html", {"form": form})


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_office(request, pk):
    exporter = get_object_or_404(Exporter, pk=pk)

    if request.method == "POST":
        form = ExporterOfficeForm(request.POST)

        if form.is_valid():
            office = form.save()
            exporter.offices.add(office)
            return redirect(
                reverse(
                    "exporter-office-edit",
                    kwargs={"exporter_pk": exporter.pk, "office_pk": office.pk},
                )
            )
    else:
        form = ExporterOfficeForm()

    context = {"object": exporter, "form": form}

    return render(request, "web/domains/exporter/create-office.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_office(request, exporter_pk, office_pk):
    exporter = get_object_or_404(Exporter, pk=exporter_pk)
    office = get_object_or_404(exporter.offices, pk=office_pk)

    if request.method == "POST":
        form = ExporterOfficeForm(request.POST, instance=office)

        if form.is_valid():
            form.save()
    else:
        form = ExporterOfficeForm(instance=office)

    context = {
        "object": exporter,
        "office": office,
        "form": form,
    }
    return render(request, "web/domains/exporter/edit-office.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def archive_office(request, exporter_pk, office_pk):
    exporter = get_object_or_404(Exporter, pk=exporter_pk)
    office = get_object_or_404(exporter.offices.filter(is_active=True), pk=office_pk)
    office.is_active = False
    office.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": exporter.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def unarchive_office(request, exporter_pk, office_pk):
    exporter = get_object_or_404(Exporter, pk=exporter_pk)
    office = get_object_or_404(exporter.offices.filter(is_active=False), pk=office_pk)
    office.is_active = True
    office.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": exporter.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_agent(request, exporter_pk):
    exporter: Exporter = get_object_or_404(Exporter, pk=exporter_pk)

    initial = {"main_exporter": exporter_pk}
    if request.method == "POST":
        form = AgentForm(request.POST, initial=initial)
        if form.is_valid():
            agent = form.save()

            return redirect(reverse("exporter-agent-edit", kwargs={"pk": agent.pk}))
    else:
        form = AgentForm(initial=initial)

    context = {
        "object": exporter,
        "form": form,
    }

    return render(request, "web/domains/exporter/create-agent.html", context=context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    exporter: Exporter = get_object_or_404(Exporter.objects.agents(), pk=pk)

    if request.method == "POST":
        form = AgentForm(request.POST, instance=exporter)
        if form.is_valid():
            exporter = form.save()

            return redirect(reverse("exporter-agent-edit", kwargs={"pk": exporter.pk}))
    else:
        form = AgentForm(instance=exporter)

    contacts = get_organisation_contacts(exporter)
    object_permissions = get_exporter_object_permissions()

    context = {
        "object": exporter.main_exporter,
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "object_permissions": object_permissions,
        "org_type": "exporter",
    }

    return render(request, "web/domains/exporter/edit-agent.html", context=context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def archive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Exporter.objects.agents().filter(is_active=True), pk=pk)
    agent.is_active = False
    agent.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": agent.main_exporter.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def unarchive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Exporter.objects.agents().filter(is_active=False), pk=pk)
    agent.is_active = True
    agent.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": agent.main_exporter.pk}))


def get_exporter_object_permissions() -> list[tuple[ExporterObjectPermissions, str]]:
    """Return object permissions for the Exporter model with a label for each."""

    object_permissions = [
        (Perms.obj.exporter.view, "View Applications / Certificates"),
        (Perms.obj.exporter.edit, "Edit Applications / Vary Certificates"),
        (Perms.obj.exporter.is_contact, "Is Exporter Contact"),
        (Perms.obj.exporter.manage_contacts_and_agents, "Approve / Reject Agents and Exporters"),
    ]

    return object_permissions
