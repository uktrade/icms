from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView
from guardian.shortcuts import get_objects_for_user

from web.domains.contacts.forms import ContactForm
from web.domains.exporter.forms import (
    AgentForm,
    AgentNonILBForm,
    ExporterFilter,
    ExporterForm,
    ExporterNonILBForm,
    ExporterUserObjectPermissionsForm,
    get_exporter_object_permissions,
)
from web.domains.office.forms import ExporterOfficeForm
from web.models import Exporter, User
from web.permissions import (
    Perms,
    can_user_edit_org,
    can_user_manage_org_contacts,
    can_user_view_org,
    is_user_org_admin,
    organisation_get_contacts,
)
from web.types import AuthenticatedHttpRequest
from web.views import ModelFilterView
from web.views.actions import Archive, CreateExporterAgent, Edit, Unarchive


class ExporterListAdminView(ModelFilterView):
    template_name = "web/domains/exporter/list.html"
    filterset_class = ExporterFilter
    model = Exporter
    permission_required = Perms.sys.exporter_admin
    page_title = "Maintain Exporters"

    # Only set when the page is first loaded.
    default_filters = {"status": True}

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


class ExporterListUserView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """Exporter list view showing all exporters the logged-in user has access to."""

    permission_required = [Perms.page.view_exporter_details]
    model = Exporter
    paginate_by = 10
    template_name = "web/domains/exporter/exporter-detail-list.html"

    extra_context = {
        "page_title": "Select an Exporter",
    }

    def get_queryset(self):
        exporter_qs = super().get_queryset().filter(is_active=True)

        required_perms = [p for p in Perms.obj.exporter.values if p != Perms.obj.exporter.is_agent]

        qs = get_objects_for_user(
            self.request.user, required_perms, klass=exporter_qs, any_perm=True
        )

        return qs.prefetch_related("offices")


@login_required
@permission_required(Perms.sys.exporter_admin, raise_exception=True)
def create_exporter(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ExporterForm(request.POST)
        if form.is_valid():
            exporter: Exporter = form.save()
            messages.info(request, "Exporter created successfully."),
            return redirect(reverse("exporter-list") + "?" + urlencode({"name": exporter.name}))
    else:
        form = ExporterForm()

    return render(request, "web/domains/exporter/create.html", {"form": form})


@login_required
def edit_exporter(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    exporter: Exporter = get_object_or_404(Exporter, pk=pk)

    # This view is for editing main exporters not agents.
    if exporter.is_agent():
        raise PermissionDenied

    if not can_user_edit_org(request.user, exporter):
        raise PermissionDenied

    form_cls = ExporterForm if is_user_org_admin(request.user, exporter) else ExporterNonILBForm
    form = form_cls(request.POST or None, instance=exporter)

    if request.method == "POST" and form.is_valid():
        exporter = form.save()
        messages.info(request, "Updated exporter details have been saved.")
        return redirect(reverse("exporter-list") + "?" + urlencode({"name": exporter.name}))

    contacts = organisation_get_contacts(exporter)
    object_permissions = get_exporter_object_permissions(exporter)
    can_manage_contacts = can_user_manage_org_contacts(request.user, exporter)

    user_context = _get_user_context(request.user)
    context = {
        "object": exporter,
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "object_permissions": object_permissions,
        "can_manage_contacts": can_manage_contacts,
        "org_type": "exporter",
    }

    return render(request, "web/domains/exporter/edit.html", context | user_context)


@require_GET
@login_required
def detail_exporter(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    exporter: Exporter = get_object_or_404(Exporter, pk=pk)

    if not can_user_view_org(request.user, exporter):
        raise PermissionDenied

    user_context = _get_user_context(request.user)
    contacts = organisation_get_contacts(exporter)
    object_permissions = get_exporter_object_permissions(exporter)

    context = {
        "object": exporter,
        "contacts": contacts,
        "object_permissions": object_permissions,
        "org_type": "exporter",
    }

    return render(request, "web/domains/exporter/detail.html", context | user_context)


@login_required
def create_office(request, pk):
    exporter = get_object_or_404(Exporter, pk=pk)

    if not can_user_edit_org(request.user, exporter):
        raise PermissionDenied

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

    user_context = _get_user_context(request.user)

    context = {
        "object": exporter,
        "form": form,
        "base_template": user_context["base_template"],
    }

    return render(request, "web/domains/exporter/create-office.html", context)


@login_required
def edit_office(request, exporter_pk, office_pk):
    exporter = get_object_or_404(Exporter, pk=exporter_pk)

    if not can_user_edit_org(request.user, exporter):
        raise PermissionDenied

    office = get_object_or_404(exporter.offices, pk=office_pk)

    if request.method == "POST":
        form = ExporterOfficeForm(request.POST, instance=office)

        if form.is_valid():
            form.save()

            return redirect(
                reverse(
                    "exporter-office-edit",
                    kwargs={"exporter_pk": exporter.pk, "office_pk": office.pk},
                )
            )
    else:
        form = ExporterOfficeForm(instance=office)

    user_context = _get_user_context(request.user)

    context = {
        "object": exporter,
        "office": office,
        "form": form,
        "base_template": user_context["base_template"],
    }
    return render(request, "web/domains/exporter/edit-office.html", context)


@login_required
@require_POST
def archive_office(request, exporter_pk, office_pk):
    exporter = get_object_or_404(Exporter, pk=exporter_pk)

    if not can_user_edit_org(request.user, exporter):
        raise PermissionDenied

    office = get_object_or_404(exporter.offices.filter(is_active=True), pk=office_pk)
    office.is_active = False
    office.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": exporter.pk}))


@login_required
@require_POST
def unarchive_office(request, exporter_pk, office_pk):
    exporter = get_object_or_404(Exporter, pk=exporter_pk)

    if not can_user_edit_org(request.user, exporter):
        raise PermissionDenied

    office = get_object_or_404(exporter.offices.filter(is_active=False), pk=office_pk)
    office.is_active = True
    office.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": exporter.pk}))


@login_required
@permission_required(Perms.sys.exporter_admin, raise_exception=True)
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
def edit_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    exporter: Exporter = get_object_or_404(Exporter.objects.agents(), pk=pk)

    if not can_user_edit_org(request.user, exporter):
        raise PermissionDenied

    form_cls = AgentForm if is_user_org_admin(request.user, exporter) else AgentNonILBForm
    form = form_cls(request.POST or None, instance=exporter)

    if request.method == "POST" and form.is_valid():
        exporter = form.save()

        return redirect(reverse("exporter-agent-edit", kwargs={"pk": exporter.pk}))

    contacts = organisation_get_contacts(exporter)
    object_permissions = get_exporter_object_permissions(exporter)
    can_manage_contacts = can_user_manage_org_contacts(request.user, exporter)
    user_context = _get_user_context(request.user)

    if can_user_edit_org(request.user, exporter.main_exporter):
        parent_url = reverse("exporter-edit", kwargs={"pk": exporter.main_exporter.pk})
        parent_url_label = exporter.name
    else:
        parent_url = reverse("user-exporter-list")
        parent_url_label = "Exporters"

    context = {
        "object": exporter.main_exporter,
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "object_permissions": object_permissions,
        "can_manage_contacts": can_manage_contacts,
        "org_type": "exporter",
        "base_template": user_context["base_template"],
        "parent_url": parent_url,
        "parent_url_label": parent_url_label,
    }

    return render(request, "web/domains/exporter/edit-agent.html", context=context)


@login_required
@permission_required(Perms.sys.exporter_admin, raise_exception=True)
@require_POST
def archive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Exporter.objects.agents().filter(is_active=True), pk=pk)
    agent.is_active = False
    agent.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": agent.main_exporter.pk}))


@login_required
@permission_required(Perms.sys.exporter_admin, raise_exception=True)
@require_POST
def unarchive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Exporter.objects.agents().filter(is_active=False), pk=pk)
    agent.is_active = True
    agent.save()

    return redirect(reverse("exporter-edit", kwargs={"pk": agent.main_exporter.pk}))


@login_required
def edit_user_exporter_permissions(
    request: AuthenticatedHttpRequest, org_pk: int, user_pk: int
) -> HttpResponse:
    """View to edit exporter object permissions for a particular user."""

    user = get_object_or_404(User, id=user_pk)
    exporter = get_object_or_404(Exporter, id=org_pk)
    can_manage_contacts = can_user_manage_org_contacts(request.user, exporter)

    if not can_manage_contacts:
        raise PermissionDenied

    form = ExporterUserObjectPermissionsForm(user, exporter, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save_obj_perms()

        return redirect("exporter-edit", pk=org_pk)

    context = {
        "page_title": "Edit Exporter user permissions",
        "org_type": "Exporter",
        "form": form,
        "contact": user,
        "organisation": exporter,
        "parent_url": reverse("exporter-edit", kwargs={"pk": org_pk}),
    }

    return render(request, "web/domains/organisation/edit-user-permissions.html", context)


def _get_user_context(user: User) -> dict[str, Any]:
    """Return common context depending on the user profile."""

    if user.has_perm(Perms.sys.exporter_admin):
        base_template = "layout/sidebar.html"
        parent_url = reverse("exporter-list")
    else:
        base_template = "layout/no-sidebar.html"
        parent_url = reverse("user-exporter-list")

    return {"base_template": base_template, "parent_url": parent_url}
