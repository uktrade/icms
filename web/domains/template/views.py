from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.urls import reverse_lazy

from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, EditTemplate, Unarchive

from .forms import (
    CFSDeclarationTranslationForm,
    EndorsementCreateTemplateForm,
    EndorsementUsageForm,
    GenericTemplate,
    TemplatesFilter,
)
from .models import EndorsementUsage, Template


class TemplateListView(ModelFilterView):
    template_name = "web/domains/template/list.html"
    model = Template
    filterset_class = TemplatesFilter
    page_title = "Maintain Templates"
    permission_required = "web.reference_data_access"

    # Default display fields on the listing page of the model
    class Display:
        fields = [
            "template_name",
            "application_domain_verbose",
            "template_type_verbose",
            "template_status",
        ]
        fields_config = {
            "template_name": {"header": "Template Name", "link": True},
            "application_domain_verbose": {"header": "Application Domain"},
            "template_type_verbose": {"header": "Template Type"},
            "template_status": {"header": "Template Status"},
        }
        actions = [Archive(), Unarchive(), EditTemplate()]


class TemplateDetailView(ModelDetailView):
    form_class = GenericTemplate
    model = Template
    permission_required = "web.reference_data_access"
    cancel_url = "javascript:history.go(-1)"


class TemplateEditView(ModelUpdateView):
    template_name = "web/domains/template/edit.html"
    form_class = GenericTemplate
    model = Template
    success_url = reverse_lazy("template-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"


class EndorsementCreateView(ModelCreateView):
    template_name = "web/domains/template/edit.html"
    form_class = EndorsementCreateTemplateForm
    model = Template
    success_url = reverse_lazy("template-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"
    page_title = "New Endorsement"

    def form_valid(self, form):
        """
        Sets readonly fields for this template type and validates other inputs.
        """
        template = form.instance

        template.template_type = Template.ENDORSEMENT
        template.application_domain = Template.IMPORT_APPLICATION

        return super().form_valid(form)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def list_endorsement_usages(request):
    usages = EndorsementUsage.objects.all()
    return render(request, "web/domains/template/list-endorsement-usages.html", {"objects": usages})


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_endorsement_usage(request, pk):
    usage = get_object_or_404(EndorsementUsage, pk=pk)
    if request.POST:
        form = EndorsementUsageForm(request.POST)
        if form.is_valid():
            linked_endorsement = form.cleaned_data["linked_endorsement"]
            usage.linked_endorsements.add(linked_endorsement)
    else:
        form = EndorsementUsageForm()

    context = {"object": usage, "form": form}
    return render(request, "web/domains/template/edit-endorsement-usage.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def archive_endorsement_usage_link(request, usage_pk, link_pk):
    usage = get_object_or_404(EndorsementUsage, pk=usage_pk)
    endorsement = get_object_or_404(Template, pk=link_pk)
    usage.linked_endorsements.remove(endorsement)

    return redirect(reverse("template-endorsement-usage-edit", kwargs={"pk": usage.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_cfs_declaration_translation(request):
    if request.POST:
        form = CFSDeclarationTranslationForm(request.POST)
        if form.is_valid():
            template = form.save()
            return redirect(
                reverse("template-cfs-declaration-translation-edit", kwargs={"pk": template.pk})
            )
    else:
        form = CFSDeclarationTranslationForm()

    return render(
        request, "web/domains/template/create-cfs-declaration-translation.html", {"form": form}
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_cfs_declaration_translation(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.POST:
        form = CFSDeclarationTranslationForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()
            return redirect(
                reverse("template-cfs-declaration-translation-edit", kwargs={"pk": template.pk})
            )
    else:
        form = CFSDeclarationTranslationForm(instance=template)

    context = {"object": template, "form": form}
    return render(request, "web/domains/template/edit-cfs-declaration-translation.html", context)
