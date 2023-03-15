from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from web.models import ImportApplicationType
from web.views import ModelCreateView, ModelFilterView
from web.views.actions import Archive, EditTemplate, Unarchive

from .forms import (
    CFSDeclarationTranslationForm,
    CFSScheduleTranslationForm,
    CFSScheduleTranslationParagraphsForm,
    DeclarationTemplateForm,
    EmailTemplateForm,
    EndorsementTemplateForm,
    EndorsementUsageForm,
    LetterFragmentForm,
    LetterTemplateForm,
    TemplatesFilter,
)
from .models import CFSScheduleParagraph, Template


class UnknownTemplateTypeException(Exception):
    pass


class TemplateListView(ModelFilterView):
    template_name = "web/domains/template/list.html"
    model = Template
    filterset_class = TemplatesFilter
    page_title = "Maintain Templates"
    permission_required = "web.ilb_admin"

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


@login_required
def view_template_fwd(request, pk):
    template = get_object_or_404(Template, pk=pk)

    if template.template_type == Template.CFS_SCHEDULE:
        return view_cfs_schedule(request, pk)
    elif template.template_type == Template.CFS_SCHEDULE_TRANSLATION:
        return view_cfs_schedule_translation(request, pk)
    else:
        return view_template(request, pk=pk)


# used for non-CFS_SCHEDULE templates
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_template(request, pk):
    template = get_object_or_404(Template, pk=pk)

    context = {"object": template, "page_title": f"Viewing {template}"}

    return render(request, "web/domains/template/detail.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_cfs_schedule(request, pk):
    template = get_object_or_404(Template, pk=pk)

    assert template.template_type == Template.CFS_SCHEDULE

    context = {"object": template}

    return render(request, "web/domains/template/view-cfs-schedule.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def view_cfs_schedule_translation(request, pk):
    template = get_object_or_404(Template, pk=pk)

    assert template.template_type == Template.CFS_SCHEDULE_TRANSLATION

    english_template = get_object_or_404(Template, template_type=Template.CFS_SCHEDULE)
    english_paras = english_template.paragraphs.all()

    assert len(english_paras) > 0

    translations = {para.name: para.content for para in template.paragraphs.all()}

    context = {
        "object": template,
        "page_title": "View CFS Schedule translation",
        "english_paras": english_paras,
        "translations": translations,
    }

    return render(request, "web/domains/template/view-cfs-schedule-translation.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_template(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if template.template_type == Template.DECLARATION:
        TemplateForm = DeclarationTemplateForm
    elif template.template_type == Template.EMAIL_TEMPLATE:
        TemplateForm = EmailTemplateForm
    elif template.template_type == Template.ENDORSEMENT:
        TemplateForm = EndorsementTemplateForm
    elif template.template_type == Template.LETTER_TEMPLATE:
        TemplateForm = LetterTemplateForm
    elif template.template_type == Template.LETTER_FRAGMENT:
        TemplateForm = LetterFragmentForm
    else:
        raise UnknownTemplateTypeException(f"Unknown template type '{template.template_type}'")

    if request.method == "POST":
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()
            return redirect(reverse("template-edit", kwargs={"pk": template.pk}))
    else:
        form = TemplateForm(instance=template)

    context = {
        "object": template,
        "form": form,
        "page_title": f"Editing {template}",
    }
    return render(request, "web/domains/template/edit.html", context)


class EndorsementCreateView(ModelCreateView):
    template_name = "web/domains/template/edit.html"
    form_class = EndorsementTemplateForm
    model = Template
    success_url = reverse_lazy("template-list")
    cancel_url = success_url
    permission_required = "web.ilb_admin"
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
@permission_required("web.ilb_admin", raise_exception=True)
def list_endorsement_usages(request):
    import_application_types = ImportApplicationType.objects.prefetch_related("endorsements")

    return render(
        request,
        "web/domains/template/list-endorsement-usages.html",
        {"objects": import_application_types},
    )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_endorsement_usage(request, pk):
    application_type = get_object_or_404(ImportApplicationType, pk=pk)
    if request.method == "POST":
        form = EndorsementUsageForm(request.POST, application_type_pk=pk)
        if form.is_valid():
            endorsement = form.cleaned_data["endorsement"]
            application_type.endorsements.add(endorsement)
    else:
        form = EndorsementUsageForm(application_type_pk=pk)

    context = {"object": application_type, "form": form}
    return render(request, "web/domains/template/edit-endorsement-usage.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def remove_endorsement_usage_link(request, application_type_pk, link_pk):
    application_type = get_object_or_404(ImportApplicationType, pk=application_type_pk)
    endorsement = get_object_or_404(Template, pk=link_pk, template_type=Template.ENDORSEMENT)
    application_type.endorsements.remove(endorsement)

    return redirect(reverse("template-endorsement-usage-edit", kwargs={"pk": application_type_pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_cfs_declaration_translation(request):
    if request.method == "POST":
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
@permission_required("web.ilb_admin", raise_exception=True)
def edit_cfs_declaration_translation(request, pk):
    template = get_object_or_404(Template, pk=pk)
    if request.method == "POST":
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


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def create_cfs_schedule_translation(request):
    if request.method == "POST":
        form = CFSScheduleTranslationForm(request.POST)

        if form.is_valid():
            template = form.save()

            return redirect(
                reverse("template-cfs-schedule-translation-edit", kwargs={"pk": template.pk})
            )
    else:
        form = CFSScheduleTranslationForm()

    context = {"form": form, "page_title": "Create CFS Schedule translation"}

    return render(request, "web/domains/template/create-cfs-schedule-translation.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_cfs_schedule_translation(request, pk):
    template = get_object_or_404(Template, pk=pk)

    assert template.template_type == Template.CFS_SCHEDULE_TRANSLATION

    english_template = get_object_or_404(Template, template_type=Template.CFS_SCHEDULE)
    english_paras = english_template.paragraphs.all()

    assert len(english_paras) > 0

    if request.method == "POST":
        form = CFSScheduleTranslationForm(request.POST, instance=template)

        if form.is_valid():
            template = form.save()

            return redirect(
                reverse("template-cfs-schedule-translation-edit", kwargs={"pk": template.pk})
            )
    else:
        form = CFSScheduleTranslationForm(instance=template)

    translations = {para.name: para.content for para in template.paragraphs.all()}

    context = {
        "object": template,
        "form": form,
        "page_title": "Edit CFS Schedule translation",
        "english_paras": english_paras,
        "translations": translations,
    }

    return render(request, "web/domains/template/edit-cfs-schedule-translation.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def edit_cfs_schedule_translation_paragraphs(request, pk):
    template = get_object_or_404(Template, pk=pk)

    assert template.template_type == Template.CFS_SCHEDULE_TRANSLATION

    english_template = get_object_or_404(Template, template_type=Template.CFS_SCHEDULE)
    english_paras = english_template.paragraphs.all()

    assert len(english_paras) > 0

    if request.method == "POST":
        form = CFSScheduleTranslationParagraphsForm(english_paras, data=request.POST)

        if form.is_valid():
            # atomically delete all old translations and insert new ones
            with transaction.atomic():
                template.paragraphs.all().delete()

                for english_para in english_paras:
                    name = f"para_{english_para.name}"

                    translation = form.cleaned_data[name]

                    CFSScheduleParagraph.objects.create(
                        template=template,
                        order=english_para.order,
                        name=english_para.name,
                        content=translation,
                    )

            return redirect(
                reverse("template-cfs-schedule-translation-edit", kwargs={"pk": template.pk})
            )
    else:
        translated_paras = list(template.paragraphs.all())
        translations = {f"para_{para.name}": para.content for para in translated_paras}

        form = CFSScheduleTranslationParagraphsForm(english_paras, initial=translations)

    context = {
        "object": template,
        "form": form,
        "page_title": "Edit CFS Schedule translation paragraphs",
    }

    return render(
        request, "web/domains/template/edit-cfs-schedule-translation-paragraphs.html", context
    )
