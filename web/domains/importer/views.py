import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from guardian.shortcuts import get_objects_for_user

from web.domains.case.forms import DocumentForm
from web.domains.contacts.forms import ContactForm
from web.domains.file.utils import create_file_model
from web.domains.importer.forms import (
    AgentIndividualForm,
    AgentOrganisationForm,
    ImporterFilter,
    ImporterIndividualForm,
    ImporterOrganisationForm,
    ImporterUserObjectPermissionsForm,
    get_importer_object_permissions,
)
from web.domains.office.forms import ImporterOfficeEORIForm, ImporterOfficeForm
from web.domains.section5.forms import ClauseQuantityForm, Section5AuthorityForm
from web.models import ClauseQuantity, Importer, Section5Authority, Section5Clause, User
from web.permissions import (
    Perms,
    add_organisation_contact,
    can_manage_org_contacts,
    get_organisation_contacts,
)
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3
from web.views import ModelFilterView
from web.views.actions import (
    Archive,
    CreateIndividualAgent,
    CreateOrganisationAgent,
    Edit,
    Unarchive,
)

logger = logging.getLogger(__name__)


class EditImporterAction(Edit):
    """The default Edit action hardcodes the url"""

    def href(self, obj):
        return reverse("importer-edit", kwargs={"pk": obj.pk})


class ImporterListAdminView(ModelFilterView):
    """ILB admin view listing all Importer records."""

    template_name = "web/domains/importer/list.html"
    filterset_class = ImporterFilter
    model = Importer
    queryset = Importer.objects.select_related("main_importer")
    page_title = "Maintain Importers"
    permission_required = "web.ilb_admin"

    class Display:
        fields = [
            "status",
            ("name", "user", "registered_number", "entity_type"),
            "offices",
            "agents",
        ]
        fields_config = {
            "name": {"header": "Importer Name", "link": True},
            "user": {"no_header": True, "link": True},
            "registered_number": {"header": "Importer Reg No"},
            "entity_type": {"header": "Importer Entity Type"},
            "status": {"header": "Status", "bold": True},
            "offices": {
                "header": "Addresses",
                "show_all": True,
                "query_filter": {"is_active": True},
            },
            "agents": {
                "header": "Agents",
                "show_all": True,
                "query_filter": {"is_active": True},
            },
        }
        opts = {"inline": True, "icon_only": True}
        actions = [
            EditImporterAction(**opts),
            CreateIndividualAgent(**opts),
            CreateOrganisationAgent(**opts),
            Archive(**opts),
            Unarchive(**opts),
        ]


class ImporterListUserView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """Importer list view showing all importers the logged-in user has access to."""

    permission_required = [Perms.page.view_importer_details]
    model = Importer
    paginate_by = 10
    template_name = "web/domains/importer/importer-detail-list.html"

    extra_context = {
        "page_title": "Select an Importer",
    }

    def get_queryset(self):
        importer_qs = super().get_queryset().filter(is_active=True)

        required_perms = [p for p in Perms.obj.importer.values if p != Perms.obj.importer.is_agent]

        qs = get_objects_for_user(
            self.request.user, required_perms, klass=importer_qs, any_perm=True
        )

        return qs.prefetch_related("offices")


# TODO: ICMSLST-1939 Update the permissions checked
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_importer(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=pk)

    if importer.type == Importer.ORGANISATION:
        ImporterForm = ImporterOrganisationForm
    elif importer.type == Importer.INDIVIDUAL:
        ImporterForm = ImporterIndividualForm
    else:
        raise NotImplementedError(f"Unknown importer type {importer.type}")

    if request.method == "POST":
        form = ImporterForm(request.POST, instance=importer)
        if form.is_valid():
            form.save()
            return redirect(reverse("importer-edit", kwargs={"pk": pk}))
    else:
        form = ImporterForm(instance=importer)

    contacts = get_organisation_contacts(importer)
    object_permissions = get_importer_object_permissions()
    can_manage_contacts = can_manage_org_contacts(importer, request.user)

    context = {
        "object": importer,
        "object_permissions": object_permissions,
        "can_manage_contacts": can_manage_contacts,
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "org_type": "importer",
    }

    return render(request, "web/domains/importer/edit.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_importer(request: AuthenticatedHttpRequest, *, entity_type: str) -> HttpResponse:
    if entity_type == "organisation":
        ImporterForm = ImporterOrganisationForm
    elif entity_type == "individual":
        ImporterForm = ImporterIndividualForm
    else:
        raise NotImplementedError(f"Unknown entity type {entity_type}")

    if request.method == "POST":
        form = ImporterForm(request.POST)
        if form.is_valid():
            importer: Importer = form.save()

            if entity_type == "individual":
                add_organisation_contact(importer, importer.user)

            return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))
    else:
        form = ImporterForm()

    context = {"form": form}

    return render(request, "web/domains/importer/create.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=pk)

    if request.method == "POST":
        form = Section5AuthorityForm(importer, request.POST, request.FILES)
        ClauseQuantityFormSet = inlineformset_factory(
            Section5Authority, ClauseQuantity, extra=0, form=ClauseQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST)

        if form.is_valid() and clause_quantity_formset.is_valid():
            section5 = form.save()

            for clause_quantity_form in clause_quantity_formset:
                clause_quantity = clause_quantity_form.save(commit=False)
                clause_quantity.section5authority = section5
                clause_quantity.save()

            return redirect(reverse("importer-section5-edit", kwargs={"pk": section5.pk}))
    else:
        form = Section5AuthorityForm(importer)

        # Create a formset to specify quantity for each section5clauses
        initial = (
            Section5Clause.objects.filter(is_active=True)
            .annotate(section5clause=F("pk"))
            .values("section5clause")
        )
        ClauseQuantityFormSet = inlineformset_factory(
            Section5Authority,
            ClauseQuantity,
            extra=len(initial),
            form=ClauseQuantityForm,
            can_delete=False,
        )
        clause_quantity_formset = ClauseQuantityFormSet(initial=initial)

    context = {
        "object": importer,
        "form": form,
        "formset": clause_quantity_formset,
    }

    return render(request, "web/domains/importer/create-section5-authority.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=pk)

    if request.method == "POST":
        ClauseQuantityFormSet = inlineformset_factory(
            Section5Authority, ClauseQuantity, extra=0, form=ClauseQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST, instance=section5)

        form = Section5AuthorityForm(
            section5.importer, request.POST, request.FILES, instance=section5
        )

        if form.is_valid() and clause_quantity_formset.is_valid():
            section5 = form.save()
            clause_quantity_formset.save()

            return redirect(reverse("importer-section5-edit", kwargs={"pk": pk}))
    else:
        form = Section5AuthorityForm(section5.importer, instance=section5)
        ClauseQuantityFormSet = inlineformset_factory(
            Section5Authority, ClauseQuantity, extra=0, form=ClauseQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(instance=section5)

    context = {
        "object": section5.importer,
        "form": form,
        "section5": section5,
        "formset": clause_quantity_formset,
    }

    return render(request, "web/domains/importer/edit-section5-authority.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    section5 = get_object_or_404(Section5Authority, pk=pk)

    context = {
        "object": section5.importer,
        "section5": section5,
    }

    return render(request, "web/domains/importer/detail-section5-authority.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def archive_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(
        Section5Authority.objects.filter(is_active=True), pk=pk
    )

    section5.is_active = False
    section5.save()

    return redirect(reverse("importer-edit", kwargs={"pk": section5.importer.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def unarchive_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(
        Section5Authority.objects.filter(is_active=False), pk=pk
    )

    section5.is_active = True
    section5.save()

    return redirect(reverse("importer-edit", kwargs={"pk": section5.importer.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def add_document_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=pk)

    if request.method == "POST":
        form = DocumentForm(data=request.POST, files=request.FILES)

        if form.is_valid():
            document = form.cleaned_data.get("document")
            create_file_model(document, request.user, section5.files)

            return redirect(reverse("importer-section5-edit", kwargs={"pk": pk}))
    else:
        form = DocumentForm()

    context = {
        "importer": section5.importer,
        "form": form,
        "section5": section5,
    }

    return render(request, "web/domains/importer/add-document-section5-authority.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_document_section5(
    request: AuthenticatedHttpRequest, section5_pk: int, document_pk: int
) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=section5_pk)

    document = section5.files.get(pk=document_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def delete_document_section5(
    request: AuthenticatedHttpRequest, section5_pk: int, document_pk: int
) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=section5_pk)

    document = section5.files.get(pk=document_pk)
    document.is_active = False
    document.save()

    return redirect(reverse("importer-section5-edit", kwargs={"pk": section5_pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_office(request, pk):
    importer = get_object_or_404(Importer, pk=pk)
    if importer.is_agent() or importer.type == Importer.INDIVIDUAL:
        form_cls = ImporterOfficeForm
    else:
        form_cls = ImporterOfficeEORIForm

    if request.method == "POST":
        form = form_cls(request.POST)

        if form.is_valid():
            office = form.save()
            importer.offices.add(office)
            return redirect(
                reverse(
                    "importer-office-edit",
                    kwargs={"importer_pk": importer.pk, "office_pk": office.pk},
                )
            )
    else:
        form = form_cls()

    context = {"object": importer, "form": form}

    return render(request, "web/domains/importer/create-office.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    office = get_object_or_404(importer.offices, pk=office_pk)
    if importer.is_agent() or importer.type == Importer.INDIVIDUAL:
        Form = ImporterOfficeForm
    else:
        Form = ImporterOfficeEORIForm

    if request.method == "POST":
        form = Form(request.POST, instance=office)
        if form.is_valid():
            form.save()
    else:
        form = Form(instance=office)

    context = {
        "object": importer,
        "office": office,
        "form": form,
    }
    return render(request, "web/domains/importer/edit-office.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def archive_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    office = get_object_or_404(importer.offices.filter(is_active=True), pk=office_pk)
    office.is_active = False
    office.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def unarchive_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    office = get_object_or_404(importer.offices.filter(is_active=False), pk=office_pk)
    office.is_active = True
    office.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_agent(
    request: AuthenticatedHttpRequest, *, importer_pk: int, entity_type: str
) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=importer_pk)

    if entity_type == "organisation":
        AgentForm = AgentOrganisationForm
    elif entity_type == "individual":
        AgentForm = AgentIndividualForm
    else:
        raise NotImplementedError(f"Unknown entity type {entity_type}")

    initial = {"main_importer": importer_pk}
    if request.method == "POST":
        form = AgentForm(request.POST, initial=initial)
        if form.is_valid():
            agent = form.save()

            if entity_type == "individual":
                add_organisation_contact(agent, agent.user)

            return redirect(reverse("importer-agent-edit", kwargs={"pk": agent.pk}))
    else:
        form = AgentForm(initial=initial)

    context = {
        "object": importer,
        "form": form,
    }

    return render(request, "web/domains/importer/create-agent.html", context=context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent: Importer = get_object_or_404(Importer.objects.agents(), pk=pk)

    if agent.is_organisation():
        AgentForm = AgentOrganisationForm
    else:
        AgentForm = AgentIndividualForm

    if request.method == "POST":
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            agent = form.save()
            return redirect(reverse("importer-agent-edit", kwargs={"pk": agent.pk}))
    else:
        form = AgentForm(instance=agent)

    contacts = get_organisation_contacts(agent)
    object_permissions = get_importer_object_permissions()
    can_manage_contacts = can_manage_org_contacts(agent, request.user)

    context = {
        "object": agent.main_importer,
        "object_permissions": object_permissions,
        "can_manage_contacts": can_manage_contacts,
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "org_type": "importer",
    }

    return render(request, "web/domains/importer/edit-agent.html", context=context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def archive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Importer.objects.agents().filter(is_active=True), pk=pk)
    agent.is_active = False
    agent.save()

    return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
@require_POST
def unarchive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Importer.objects.agents().filter(is_active=False), pk=pk)
    agent.is_active = True
    agent.save()

    return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def importer_detail_view(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=pk)

    contacts = get_organisation_contacts(importer)
    object_permissions = get_importer_object_permissions()

    context = {
        "object": importer,
        "object_permissions": object_permissions,
        "contacts": contacts,
        "org_type": "importer",
    }

    return render(request, "web/domains/importer/view.html", context)


@login_required
@permission_required(Perms.page.view_edit_importer, raise_exception=True)
def edit_user_importer_permissions(
    request: AuthenticatedHttpRequest, org_pk: int, user_pk: int
) -> HttpResponse:
    """View to edit importer object permissions for a particular user."""

    user = get_object_or_404(User, id=user_pk)
    importer = get_object_or_404(Importer, id=org_pk)
    can_manage_contacts = can_manage_org_contacts(importer, request.user)

    if not can_manage_contacts:
        raise PermissionDenied

    form = ImporterUserObjectPermissionsForm(user, importer, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save_obj_perms()

        return redirect("importer-edit", pk=org_pk)

    context = {
        "page_title": "Edit Importer user permissions",
        "org_type": "Importer",
        "form": form,
        "contact": user,
        "organisation": importer,
        "parent_url": reverse("importer-edit", kwargs={"pk": org_pk}),
    }

    return render(request, "web/domains/organisation/edit-user-permissions.html", context)
