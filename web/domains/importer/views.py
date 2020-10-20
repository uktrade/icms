import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.views.generic import View
from guardian.shortcuts import assign_perm, get_users_with_perms, remove_perm

from web.address.address import find as postcode_lookup
from web.company.companieshouse import api_get_companies
from web.domains.importer.forms import (
    AgentIndividualForm,
    AgentOrganisationForm,
    ImporterFilter,
    ImporterIndividualDisplayForm,
    ImporterIndividualForm,
    ImporterOrganisationDisplayForm,
    ImporterOrganisationForm,
)
from web.domains.importer.models import Importer
from web.domains.office.forms import OfficeForm, OfficeEORIForm
from web.domains.user.forms import ContactForm
from web.domains.user.models import User
from web.views import ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, CreateAgent, Edit, Unarchive

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
            "name": {"header": "Importer Name", "link": True,},
            "user": {"no_header": True, "link": True},
            "registered_number": {"header": "Importer Reg No",},
            "entity_type": {"header": "Importer Entity Type",},
            "status": {"header": "Status", "bold": True,},
            "offices": {"header": "Addresses", "show_all": True,},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [Archive(**opts), Unarchive(**opts), CreateAgent(**opts), Edit(**opts)]


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
        assign_perm("web.is_contact_of_importer", contact, importer)
    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
# TODO: permissions - importer's contacts should be able to manage contacts
@require_POST
def delete_contact(request, importer_pk, contact_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    contact = get_object_or_404(User, pk=contact_pk)

    remove_perm("web.is_contact_of_importer", contact, importer)
    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_office(request, pk):
    importer = get_object_or_404(Importer, pk=pk)
    if importer.is_organisation():
        Form = OfficeEORIForm
    else:
        Form = OfficeForm

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
    if importer.is_organisation():
        Form = OfficeEORIForm
    else:
        Form = OfficeForm

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


class AgentCreateView(ModelUpdateView):
    def get_context_data(self, *args, **kwargs):
        kwargs["page_title"] = "Agent"
        kwargs["importer"] = Importer.objects.get(pk=self.kwargs["importer_id"])
        return super().get_context_data(*args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["main_importer"] = self.kwargs["importer_id"]
        return initial


class AgentEditView(ModelUpdateView):
    queryset = Importer.objects.filter(main_importer__isnull=False)
    template_name = "web/domains/importer/create.html"

    def get_form_class(self):
        agent = self.get_object()
        if agent.is_organisation():
            return AgentOrganisationForm
        return AgentIndividualForm


class AgentArchiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    queryset = Importer.objects.filter(main_importer__isnull=False)
    http_method_names = ["get"]
    permission_required = "web.reference_data_access"

    def get(self, request, *args, **kwargs):
        agent = get_object_or_404(self.queryset, pk=kwargs["pk"])
        agent.is_active = False
        agent.save()
        return redirect(reverse_lazy("importer-agent-edit", kwargs=kwargs))


class AgentUnArchiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    queryset = Importer.objects.filter(main_importer__isnull=False)
    http_method_names = ["get"]
    permission_required = "web.reference_data_access"

    def get(self, request, *args, **kwargs):
        agent = get_object_or_404(self.queryset, pk=kwargs["pk"])
        agent.is_active = True
        agent.save()
        return redirect(reverse_lazy("importer-agent-edit", kwargs=kwargs))


class ImporterOrganisationDetailView(ModelDetailView):
    template_name = "web/domains/importer/view.html"
    form_class = ImporterOrganisationDisplayForm
    model = Importer
    permission_required = "web.reference_data_access"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ImporterOrganisationDisplayForm(instance=self.get_object())

        importer_contacts = get_users_with_perms(
            self.object, only_with_perms_in=["is_contact_of_importer"]
        ).filter(user_permissions__codename="importer_access")
        context["contacts"] = importer_contacts

        return context


class ImporterIndividualDetailView(ModelDetailView):
    template_name = "web/domains/importer/view.html"
    form_class = ImporterIndividualDisplayForm
    model = Importer
    permission_required = "web.reference_data_access"

    def get_context_data(self, object):
        context = super().get_context_data(object)

        form = ImporterIndividualDisplayForm(instance=object)
        user = object.user

        if user:
            form.initial["user_title"] = user.title
            form.initial["user_first_name"] = user.first_name
            form.initial["user_last_name"] = user.last_name
            form.initial["user_email"] = user.email
            form.initial["user_tel_no"] = "\n".join(
                f"{x.phone} ({x.entity_type})" for x in user.phone_numbers.all()
            )

        context["form"] = form

        importer_contacts = get_users_with_perms(
            self.object, only_with_perms_in=["is_contact_of_importer"]
        ).filter(user_permissions__codename="importer_access")
        context["contacts"] = importer_contacts

        return context


def importer_detail_view(request, pk):
    importer = Importer.objects.get(pk=pk)

    # there might be a better way to dynamically switch which view we're using
    # depending on the object type, but this works
    if importer.is_organisation():
        view = ImporterOrganisationDetailView.as_view()
    else:
        view = ImporterIndividualDetailView.as_view()

    return view(request, pk=pk)


def list_postcode_addresses(request,):
    postcode = request.POST.get("postcode")

    return JsonResponse(postcode_lookup(postcode), safe=False)


def list_companies(request):
    query = request.POST.get("query")
    companies = api_get_companies(query)

    return JsonResponse(companies, safe=False)
