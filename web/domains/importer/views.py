import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import F
from django.forms.models import inlineformset_factory
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from guardian.shortcuts import assign_perm, get_users_with_perms, remove_perm

from web.address.address import find as postcode_lookup
from web.company.companieshouse import api_get_companies
from web.domains.file.utils import create_file_model
from web.domains.importer.forms import (
    AgentIndividualForm,
    AgentOrganisationForm,
    ImporterFilter,
    ImporterIndividualForm,
    ImporterOrganisationForm,
)
from web.domains.importer.models import Importer
from web.domains.office.forms import OfficeEORIForm, OfficeForm
from web.domains.section5.forms import (
    ClauseQuantityForm,
    DocumentForm,
    Section5AuthorityForm,
)
from web.domains.section5.models import (
    ClauseQuantity,
    Section5Authority,
    Section5Clause,
)
from web.domains.user.forms import ContactForm
from web.domains.user.models import User
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


class ImporterListView(ModelFilterView):
    template_name = "web/domains/importer/list.html"
    filterset_class = ImporterFilter
    model = Importer
    queryset = Importer.objects.prefetch_related("offices").select_related("main_importer")
    page_title = "Maintain Importers"
    permission_required = "web.reference_data_access"

    class Display:
        fields = ["status", ("name", "user", "registered_number", "entity_type"), "offices"]
        fields_config = {
            "name": {"header": "Importer Name", "link": True},
            "user": {"no_header": True, "link": True},
            "registered_number": {"header": "Importer Reg No"},
            "entity_type": {"header": "Importer Entity Type"},
            "status": {"header": "Status", "bold": True},
            "offices": {"header": "Addresses", "show_all": True},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [
            Edit(**opts),
            CreateIndividualAgent(**opts),
            CreateOrganisationAgent(**opts),
            Archive(**opts),
            Unarchive(**opts),
        ]


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_importer(request, pk):
    importer = get_object_or_404(Importer, pk=pk)

    if importer.is_organisation():
        ImporterForm = ImporterOrganisationForm
    else:
        ImporterForm = ImporterIndividualForm

    if request.POST:
        form = ImporterForm(request.POST, instance=importer)
        if form.is_valid():
            form.save()
            return redirect(reverse("importer-edit", kwargs={"pk": pk}))
    else:
        form = ImporterForm(instance=importer)

    importer_contacts = get_users_with_perms(
        importer, only_with_perms_in=["is_contact_of_importer"]
    ).filter(user_permissions__codename="importer_access")
    available_contacts = User.objects.importer_access().exclude(pk__in=importer_contacts)
    if importer.type == Importer.INDIVIDUAL:
        available_contacts = available_contacts.exclude(pk=importer.user.pk)

    context = {
        "object": importer,
        "form": form,
        "contact_form": ContactForm(available_contacts),
        "contacts": importer_contacts,
    }
    return render(request, "web/domains/importer/edit.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_importer(request, entity):
    if entity == "organisation":
        ImporterForm = ImporterOrganisationForm
    else:
        ImporterForm = ImporterIndividualForm

    if request.POST:
        form = ImporterForm(request.POST)
        if form.is_valid():
            importer = form.save()
            return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))
    else:
        form = ImporterForm()

    context = {
        "form": form,
    }

    return render(request, "web/domains/importer/create.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
# TODO: permissions - importer's contacts should be able to manage contacts
@require_POST
def add_contact(request, pk):
    importer = get_object_or_404(Importer, pk=pk)
    available_contacts = User.objects.importer_access()
    form = ContactForm(available_contacts, request.POST)
    if form.is_valid():
        contact = form.cleaned_data["contact"]
        if importer.is_agent():
            assign_perm("web.is_agent_of_importer", contact, importer.main_importer)
        else:
            assign_perm("web.is_contact_of_importer", contact, importer)

    if importer.is_agent():
        return redirect(reverse("importer-agent-edit", kwargs={"pk": importer.pk}))
    else:
        return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_section5(request: HttpRequest, pk: int) -> HttpResponse:
    importer: Importer = get_object_or_404(Importer, pk=pk)

    if request.POST:
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
        initial = Section5Clause.objects.annotate(section5clause=F("pk")).values("section5clause")
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
@permission_required("web.reference_data_access", raise_exception=True)
def edit_section5(request: HttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=pk)

    if request.POST:
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
@permission_required("web.reference_data_access", raise_exception=True)
def view_section5(request: HttpRequest, pk: int) -> HttpResponse:
    section5 = get_object_or_404(Section5Authority, pk=pk)

    context = {
        "object": section5.importer,
        "section5": section5,
    }

    return render(request, "web/domains/importer/detail-section5-authority.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_section5(request: HttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(
        Section5Authority.objects.filter(is_active=True), pk=pk
    )

    section5.is_active = False
    section5.save()

    return redirect(reverse("importer-edit", kwargs={"pk": section5.importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def unarchive_section5(request: HttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(
        Section5Authority.objects.filter(is_active=False), pk=pk
    )

    section5.is_active = True
    section5.save()

    return redirect(reverse("importer-edit", kwargs={"pk": section5.importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_document_section5(request: HttpRequest, pk: int) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=pk)

    if request.POST:
        form = DocumentForm(data=request.POST, files=request.FILES)
        document = request.FILES.get("document")

        if form.is_valid():
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
@permission_required("web.reference_data_access", raise_exception=True)
def view_document_section5(
    request: HttpRequest, section5_pk: int, document_pk: int
) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=section5_pk)

    document = section5.files.get(pk=document_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def delete_document_section5(
    request: HttpRequest, section5_pk: int, document_pk: int
) -> HttpResponse:
    section5: Section5Authority = get_object_or_404(Section5Authority, pk=section5_pk)

    document = section5.files.get(pk=document_pk)
    document.is_active = False
    document.save()

    return redirect(reverse("importer-section5-edit", kwargs={"pk": section5_pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
# TODO: permissions - importer's contacts should be able to manage contacts
@require_POST
def delete_contact(request, importer_pk, contact_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    contact = get_object_or_404(User, pk=contact_pk)

    if importer.is_agent():
        remove_perm("web.is_agent_of_importer", contact, importer.main_importer)
        return redirect(reverse("importer-agent-edit", kwargs={"pk": importer.pk}))
    else:
        remove_perm("web.is_contact_of_importer", contact, importer)
        return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_office(request, pk):
    importer = get_object_or_404(Importer, pk=pk)
    if importer.is_agent() or importer.type == Importer.INDIVIDUAL:
        Form = OfficeForm
    else:
        Form = OfficeEORIForm

    if request.POST:
        form = Form(request.POST)
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
        form = Form()

    context = {"object": importer, "form": form}

    return render(request, "web/domains/importer/create-office.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    office = get_object_or_404(importer.offices, pk=office_pk)
    if importer.is_agent() or importer.type == Importer.INDIVIDUAL:
        Form = OfficeForm
    else:
        Form = OfficeEORIForm

    if request.POST:
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
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    office = get_object_or_404(importer.offices.filter(is_active=True), pk=office_pk)
    office.is_active = False
    office.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def unarchive_office(request, importer_pk, office_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    office = get_object_or_404(importer.offices.filter(is_active=False), pk=office_pk)
    office.is_active = True
    office.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_agent(request, importer_pk, entity):
    importer = get_object_or_404(Importer, pk=importer_pk)
    initial = {"main_importer": importer_pk}
    if entity == "organisation":
        AgentForm = AgentOrganisationForm
    else:
        AgentForm = AgentIndividualForm

    if request.POST:
        form = AgentForm(request.POST, initial=initial)
        if form.is_valid():
            agent = form.save()
            return redirect(reverse("importer-agent-edit", kwargs={"pk": agent.pk}))
    else:
        form = AgentForm(initial=initial)

    context = {
        "object": importer,
        "form": form,
    }

    return render(request, "web/domains/importer/create-agent.html", context=context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_agent(request, pk):
    agent = get_object_or_404(Importer.objects.agents(), pk=pk)
    if agent.is_organisation():
        AgentForm = AgentOrganisationForm
    else:
        AgentForm = AgentIndividualForm

    if request.POST:
        form = AgentForm(request.POST, instance=agent)
        if form.is_valid():
            agent = form.save()
            return redirect(reverse("importer-agent-edit", kwargs={"pk": agent.pk}))
    else:
        form = AgentForm(instance=agent)

    agent_contacts = get_users_with_perms(
        agent.main_importer, only_with_perms_in=["is_agent_of_importer"]
    ).filter(user_permissions__codename="importer_access")
    available_contacts = User.objects.importer_access().exclude(pk__in=agent_contacts)

    context = {
        "object": agent.main_importer,
        "form": form,
        "contact_form": ContactForm(available_contacts),
        "contacts": agent_contacts,
    }

    return render(request, "web/domains/importer/edit-agent.html", context=context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_agent(self, pk):
    agent = get_object_or_404(Importer.objects.agents().filter(is_active=True), pk=pk)
    agent.is_active = False
    agent.save()

    if agent.type == Importer.INDIVIDUAL:
        remove_perm("web.is_agent_of_importer", agent.user, agent.main_importer)

    return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def unarchive_agent(self, pk):
    agent = get_object_or_404(Importer.objects.agents().filter(is_active=False), pk=pk)
    agent.is_active = True
    agent.save()

    if agent.type == Importer.INDIVIDUAL:
        assign_perm("web.is_agent_of_importer", agent.user, agent.main_importer)

    return redirect(reverse("importer-edit", kwargs={"pk": agent.main_importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def importer_detail_view(request, pk):
    importer = get_object_or_404(Importer, pk=pk)
    contacts = get_users_with_perms(importer, only_with_perms_in=["is_contact_of_importer"]).filter(
        user_permissions__codename="importer_access"
    )

    context = {
        "object": importer,
        "contacts": contacts,
    }
    return render(request, "web/domains/importer/view.html", context)


def list_postcode_addresses(request):
    postcode = request.POST.get("postcode")

    return JsonResponse(postcode_lookup(postcode), safe=False)


def list_companies(request):
    query = request.POST.get("query")
    companies = api_get_companies(query)

    return JsonResponse(companies, safe=False)
