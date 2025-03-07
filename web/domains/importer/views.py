import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView
from guardian.shortcuts import get_objects_for_user

from web.domains.case.forms import DocumentForm
from web.domains.contacts.forms import ContactForm
from web.domains.file.utils import create_file_model
from web.domains.importer.forms import (
    AgentIndividualForm,
    AgentIndividualNonILBForm,
    AgentOrganisationForm,
    AgentOrganisationNonILBForm,
    ArchiveSection5AuthorityForm,
    ImporterFilter,
    ImporterIndividualForm,
    ImporterIndividualNonILBForm,
    ImporterOrganisationForm,
    ImporterOrganisationNonILBForm,
    ImporterUserObjectPermissionsForm,
    get_importer_object_permissions,
)
from web.domains.office.forms import ImporterOfficeEORIForm, ImporterOfficeForm
from web.domains.section5.forms import ClauseQuantityForm, Section5AuthorityForm
from web.mail.emails import send_authority_archived_email
from web.models import ClauseQuantity, Importer, Section5Authority, Section5Clause, User
from web.permissions import (
    Perms,
    can_user_edit_firearm_authorities,
    can_user_edit_org,
    can_user_edit_section5_authorities,
    can_user_manage_org_contacts,
    can_user_view_org,
    is_user_org_admin,
    organisation_add_contact,
    organisation_get_contacts,
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


def get_importer_list_fields() -> list[Any]:
    return [
        "status",
        ("name", "user", "registered_number", "entity_type"),
        "offices",
        "agents",
    ]


def get_importer_list_fields_config() -> dict[str, Any]:
    return {
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


class ImporterListAdminView(ModelFilterView):
    """ILB admin view listing all Importer records."""

    template_name = "web/domains/importer/list.html"
    filterset_class = ImporterFilter
    # Only set when the page is first loaded.
    default_filters = {"status": True}

    model = Importer
    queryset = Importer.objects.select_related("main_importer")
    page_title = "Maintain Importers"
    permission_required = Perms.sys.importer_admin

    class Display:
        fields = get_importer_list_fields()
        fields_config = get_importer_list_fields_config()

        opts = {"inline": True, "icon_only": True}
        actions = [
            EditImporterAction(**opts),
            CreateIndividualAgent(**opts),
            CreateOrganisationAgent(**opts),
            Archive(**opts),
            Unarchive(**opts),
        ]


class ImporterListUserView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
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


class ImporterListRegulatorView(ModelFilterView):
    """Importer list view used by several groups.

    Groups:
      - Home Office Case Officer
      - Constabulary Contact
      - NCA Case Officer
    """

    # PermissionRequiredMixin config
    permission_required = Perms.sys.importer_regulator

    # ListView config
    model = Importer
    queryset = Importer.objects.select_related("main_importer")
    template_name = "web/domains/importer/reg-list.html"

    # ModelFilterView config
    page_title = "Maintain Importers"
    filterset_class = ImporterFilter
    # Only set when the page is first loaded.
    default_filters = {"status": True}

    class Display:
        fields = get_importer_list_fields()
        fields_config = get_importer_list_fields_config()
        actions: list[Any] = []


class ImporterDetailRegulatorView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Importer detail view used by several groups.

    Groups:
      - Home Office Case Officer
      - Constabulary Contact
      - NCA Case Officer
    """

    permission_required = Perms.sys.importer_regulator

    model = Importer
    pk_url_kwarg = "importer_pk"
    http_method_names = ["get"]
    template_name = "web/domains/importer/reg-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": "View Importer",
            "parent_url": reverse("regulator-importer-list"),
            "is_main_importer": not self.object.is_agent(),
            "can_edit_firearm_authorities": can_user_edit_firearm_authorities(self.request.user),
            "can_edit_section5_authorities": can_user_edit_section5_authorities(self.request.user),
        }


@login_required
@permission_required(Perms.sys.importer_admin, raise_exception=True)
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
                organisation_add_contact(importer, importer.user, assign_manage=True)

            messages.info(request, "Importer created successfully.")
            return redirect(reverse("importer-list") + "?" + urlencode({"name": importer.name}))
    else:
        form = ImporterForm()

    context = {"form": form}

    return render(request, "web/domains/importer/create.html", context)


@login_required
def edit_importer(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=pk)

    # This view is for editing main importers not agents.
    if importer.is_agent():
        raise PermissionDenied

    if not can_user_edit_org(request.user, importer):
        raise PermissionDenied

    match (importer.type, is_user_org_admin(request.user, importer)):
        case Importer.ORGANISATION, True:
            form_cls = ImporterOrganisationForm
        case Importer.ORGANISATION, False:
            form_cls = ImporterOrganisationNonILBForm
        case Importer.INDIVIDUAL, True:
            form_cls = ImporterIndividualForm
        case Importer.INDIVIDUAL, False:
            form_cls = ImporterIndividualNonILBForm
        case _:
            raise NotImplementedError(f"Unknown importer type {importer.type}")

    form = form_cls(request.POST or None, instance=importer)

    if request.method == "POST" and form.is_valid():
        form.save()
        if (
            not form.cleaned_data.get("eori_number")
            and not form.instance.eori_number
            and is_user_org_admin(request.user, importer)
        ):
            # If the user is an admin and the importer does not have an EORI number, show a warning message asking
            # them to provide one ASAP
            messages.warning(
                request,
                "An EORI number is required to progress an application from this importer, "
                "please provide one as soon as possible.",
            )
        else:
            messages.info(request, "Updated importer details have been saved.")
        if request.user.has_perm(Perms.sys.importer_admin):
            return redirect(reverse("importer-list") + "?" + urlencode({"name": importer.name}))
        else:
            return redirect(reverse("user-importer-list"))

    contacts = organisation_get_contacts(importer)
    object_permissions = get_importer_object_permissions(importer)
    can_manage_contacts = can_user_manage_org_contacts(request.user, importer)

    context = {
        "object": importer,
        "object_permissions": object_permissions,
        "can_manage_contacts": can_manage_contacts,
        "is_user_org_admin": is_user_org_admin(request.user, importer),
        "show_firearm_authorities": can_user_edit_firearm_authorities(request.user),
        "show_section5_authorities": can_user_edit_section5_authorities(request.user),
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "org_type": "importer",
    }

    user_context = _get_user_context(request.user)

    return render(request, "web/domains/importer/edit.html", context | user_context)


@login_required
def create_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user):
        raise PermissionDenied

    importer: Importer = get_object_or_404(Importer, pk=pk)

    if request.method == "POST":
        form = Section5AuthorityForm(importer, request.POST, request.FILES, can_upload_files=True)
        ClauseQuantityFormSet = inlineformset_factory(
            Section5Authority, ClauseQuantity, extra=0, form=ClauseQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST)

        if form.is_valid() and clause_quantity_formset.is_valid():
            section5 = form.save()
            if uploaded_files := form.cleaned_data["documents"]:
                for file in uploaded_files:
                    create_file_model(file, request.user, section5.files)

            for clause_quantity_form in clause_quantity_formset:
                clause_quantity = clause_quantity_form.save(commit=False)
                clause_quantity.section5authority = section5
                clause_quantity.save()

            messages.success(request, "Section 5 Authority created successfully.")

            return redirect(reverse("importer-section5-edit", kwargs={"pk": section5.pk}))
    else:
        form = Section5AuthorityForm(importer, can_upload_files=True)

        # Create a formset to specify quantity for each section5 clauses
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

    user_context = _get_section_5_user_context(request.user, importer)

    return render(
        request, "web/domains/importer/create-section5-authority.html", context | user_context
    )


@login_required
def edit_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user):
        raise PermissionDenied

    section5: Section5Authority = get_object_or_404(Section5Authority, pk=pk)

    if request.method == "POST":
        ClauseQuantityFormSet = inlineformset_factory(
            Section5Authority, ClauseQuantity, extra=0, form=ClauseQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST, instance=section5)

        form = Section5AuthorityForm(
            section5.importer,
            request.POST,
            request.FILES,
            instance=section5,
            can_upload_files=False,
        )

        if form.is_valid() and clause_quantity_formset.is_valid():
            form.save()
            clause_quantity_formset.save()

            return redirect(reverse("importer-section5-edit", kwargs={"pk": pk}))
    else:
        form = Section5AuthorityForm(section5.importer, instance=section5, can_upload_files=False)
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

    user_context = _get_section_5_user_context(request.user, section5.importer)

    return render(
        request, "web/domains/importer/edit-section5-authority.html", context | user_context
    )


@login_required
@require_GET
def view_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user) and not request.user.has_perm(
        Perms.sys.importer_regulator
    ):
        raise PermissionDenied

    section5 = get_object_or_404(Section5Authority, pk=pk)

    context = {
        "object": section5.importer,
        "section5": section5,
    }
    user_context = _get_section_5_user_context(request.user, section5.importer)

    return render(
        request, "web/domains/importer/detail-section5-authority.html", context | user_context
    )


@login_required
def archive_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user):
        raise PermissionDenied

    section5: Section5Authority = get_object_or_404(
        Section5Authority.objects.filter(is_active=True), pk=pk
    )

    if request.method == "POST":
        form = ArchiveSection5AuthorityForm(request.POST, instance=section5)

        if form.is_valid():
            section5 = form.save(commit=False)
            section5.is_active = False
            section5.save()

            send_authority_archived_email(section5)
            redirect_to = _get_section_5_redirect_url(request.user, section5.importer)
            return redirect(redirect_to)
    else:
        form = ArchiveSection5AuthorityForm(instance=section5)

    context = {
        "object": section5.importer,
        "section5": section5,
        "form": form,
    }
    user_context = _get_section_5_user_context(request.user, section5.importer)

    return render(
        request, "web/domains/importer/archive-section5-authority.html", context | user_context
    )


@login_required
@require_POST
def unarchive_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user):
        raise PermissionDenied

    section5: Section5Authority = get_object_or_404(
        Section5Authority.objects.filter(is_active=False), pk=pk
    )

    section5.is_active = True
    section5.archive_reason = None
    section5.other_archive_reason = None
    section5.save()

    redirect_to = _get_section_5_redirect_url(request.user, section5.importer)
    return redirect(redirect_to)


@login_required
def add_document_section5(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user):
        raise PermissionDenied

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
    user_context = _get_section_5_user_context(request.user, section5.importer)

    return render(
        request, "web/domains/importer/add-document-section5-authority.html", context | user_context
    )


@login_required
@require_GET
def view_document_section5(
    request: AuthenticatedHttpRequest, section5_pk: int, document_pk: int
) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user) and not request.user.has_perm(
        Perms.sys.importer_regulator
    ):
        raise PermissionDenied

    section5: Section5Authority = get_object_or_404(Section5Authority, pk=section5_pk)

    document = section5.files.get(pk=document_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@require_POST
def delete_document_section5(
    request: AuthenticatedHttpRequest, section5_pk: int, document_pk: int
) -> HttpResponse:
    if not can_user_edit_section5_authorities(request.user):
        raise PermissionDenied

    section5: Section5Authority = get_object_or_404(Section5Authority, pk=section5_pk)

    document = section5.files.get(pk=document_pk)
    document.is_active = False
    document.save()

    return redirect(reverse("importer-section5-edit", kwargs={"pk": section5_pk}))


def _get_section_5_redirect_url(user: User, importer: Importer) -> str:
    """Used when archiving / un-archiving section5 authorities."""

    if user.has_perm(Perms.sys.importer_admin):
        return reverse("importer-edit", kwargs={"pk": importer.pk})
    elif user.has_perm(Perms.sys.importer_regulator):
        return reverse("regulator-importer-detail", kwargs={"importer_pk": importer.pk})

    raise ValueError(f"Unknown section5 redirect for user: {user}")


def _get_section_5_user_context(user: User, importer: Importer) -> dict[str, Any]:
    """Return common context depending on the user profile for the section 5 views."""

    if user.has_perm(Perms.sys.importer_admin):
        base_template = "layout/sidebar.html"
        parent_url = reverse("importer-edit", kwargs={"pk": importer.pk})
    elif user.has_perm(Perms.sys.importer_regulator):
        base_template = "layout/no-sidebar.html"
        parent_url = reverse("regulator-importer-detail", kwargs={"importer_pk": importer.pk})
    else:
        raise ValueError(f"Unknown section5 context for user: {user}")

    return {"base_template": base_template, "parent_url": parent_url}


@login_required
def create_office(request, pk):
    importer = get_object_or_404(Importer, pk=pk)

    if not can_user_edit_org(request.user, importer):
        raise PermissionDenied

    if importer.is_agent() or importer.type == Importer.INDIVIDUAL:
        form_cls = ImporterOfficeForm
    else:
        form_cls = ImporterOfficeEORIForm

    if request.method == "POST":
        form = form_cls(request.POST)

        if form.is_valid():
            office = form.save()
            importer.offices.add(office)
            messages.success(request, "Office created successfully.")
            return redirect(
                reverse(
                    "importer-edit",
                    kwargs={"pk": importer.pk},
                )
            )
    else:
        form = form_cls()

    user_context = _get_user_context(request.user)

    context = {
        "object": importer,
        "form": form,
        "base_template": user_context["base_template"],
    }

    return render(request, "web/domains/importer/create-office.html", context)


@login_required
def edit_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)

    if not can_user_edit_org(request.user, importer):
        raise PermissionDenied

    office = get_object_or_404(importer.offices, pk=office_pk)
    if importer.is_agent() or importer.type == Importer.INDIVIDUAL:
        Form = ImporterOfficeForm
    else:
        Form = ImporterOfficeEORIForm

    if request.method == "POST":
        form = Form(request.POST, instance=office)
        if form.is_valid():
            form.save()

            return redirect(
                reverse(
                    "importer-office-edit",
                    kwargs={"importer_pk": importer.pk, "office_pk": office.pk},
                )
            )
    else:
        form = Form(instance=office)

    user_context = _get_user_context(request.user)

    context = {
        "object": importer,
        "office": office,
        "form": form,
        "base_template": user_context["base_template"],
    }
    return render(request, "web/domains/importer/edit-office.html", context)


@login_required
@require_POST
def archive_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)

    if not can_user_edit_org(request.user, importer):
        raise PermissionDenied

    office = get_object_or_404(importer.offices.filter(is_active=True), pk=office_pk)
    office.is_active = False
    office.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@require_POST
def unarchive_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)

    if not can_user_edit_org(request.user, importer):
        raise PermissionDenied

    office = get_object_or_404(importer.offices.filter(is_active=False), pk=office_pk)
    office.is_active = True
    office.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required(Perms.sys.importer_admin, raise_exception=True)
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
                organisation_add_contact(agent, agent.user, assign_manage=False)

            return redirect(reverse("importer-agent-edit", kwargs={"pk": agent.pk}))
    else:
        form = AgentForm(initial=initial)

    context = {
        "object": importer,
        "form": form,
    }

    return render(request, "web/domains/importer/create-agent.html", context=context)


@login_required
def edit_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent: Importer = get_object_or_404(Importer.objects.agents(), pk=pk)

    if not can_user_edit_org(request.user, agent):
        raise PermissionDenied

    match (agent.type, is_user_org_admin(request.user, agent)):
        case Importer.ORGANISATION, True:
            form_cls = AgentOrganisationForm
        case Importer.ORGANISATION, False:
            form_cls = AgentOrganisationNonILBForm
        case Importer.INDIVIDUAL, True:
            form_cls = AgentIndividualForm
        case Importer.INDIVIDUAL, False:
            form_cls = AgentIndividualNonILBForm
        case _:
            raise NotImplementedError(f"Unknown importer type {agent.type}")

    if request.method == "POST":
        form = form_cls(request.POST, instance=agent)
        if form.is_valid():
            agent = form.save()
            messages.info(request, "Updated agent details have been saved.")
            return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))
    else:
        form = form_cls(instance=agent)

    contacts = organisation_get_contacts(agent)
    object_permissions = get_importer_object_permissions(agent)
    can_manage_contacts = can_user_manage_org_contacts(request.user, agent)

    user_context = _get_user_context(request.user)

    if can_user_edit_org(request.user, agent.main_importer):
        parent_url = reverse("importer-edit", kwargs={"pk": agent.main_importer.pk})
        parent_url_label = agent.main_importer.display_name
    else:
        parent_url = reverse("user-importer-list")
        parent_url_label = "Importers"

    context = {
        "object": agent.main_importer,
        "object_permissions": object_permissions,
        "can_manage_contacts": can_manage_contacts,
        "is_user_org_admin": is_user_org_admin(request.user, agent),
        "form": form,
        "contact_form": ContactForm(contacts_to_exclude=contacts),
        "contacts": contacts,
        "org_type": "importer",
        "base_template": user_context["base_template"],
        "parent_url": parent_url,
        "parent_url_label": parent_url_label,
    }

    return render(request, "web/domains/importer/edit-agent.html", context=context)


@login_required
@permission_required(Perms.sys.importer_admin, raise_exception=True)
@require_POST
def archive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Importer.objects.agents().filter(is_active=True), pk=pk)
    agent.is_active = False
    agent.save()

    return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))


@login_required
@permission_required(Perms.sys.importer_admin, raise_exception=True)
@require_POST
def unarchive_agent(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    agent = get_object_or_404(Importer.objects.agents().filter(is_active=False), pk=pk)
    agent.is_active = True
    agent.save()

    return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))


@login_required
@require_GET
def importer_detail_view(request: AuthenticatedHttpRequest, *, pk: int) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=pk)

    if not can_user_view_org(request.user, importer):
        raise PermissionDenied

    contacts = organisation_get_contacts(importer)
    object_permissions = get_importer_object_permissions(importer)

    context = {
        "object": importer,
        "object_permissions": object_permissions,
        "show_firearm_authorities": can_user_edit_firearm_authorities(request.user),
        "show_section5_authorities": can_user_edit_section5_authorities(request.user),
        "contacts": contacts,
        "org_type": "importer",
    }

    user_context = _get_user_context(request.user)

    return render(request, "web/domains/importer/view.html", context | user_context)


@login_required
def edit_user_importer_permissions(
    request: AuthenticatedHttpRequest, org_pk: int, user_pk: int
) -> HttpResponse:
    """View to edit importer object permissions for a particular user."""

    user = get_object_or_404(User, id=user_pk)
    importer = get_object_or_404(Importer, id=org_pk)

    if not can_user_manage_org_contacts(request.user, importer):
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


def _get_user_context(user: User) -> dict[str, Any]:
    """Return common context depending on the user profile."""

    if user.has_perm(Perms.sys.importer_admin):
        base_template = "layout/sidebar.html"
        parent_url = reverse("importer-list")
        show_content_actions = False
    else:
        base_template = "layout/no-sidebar.html"
        parent_url = reverse("user-importer-list")
        show_content_actions = True

    return {
        "base_template": base_template,
        "parent_url": parent_url,
        "show_content_actions": show_content_actions,
    }
