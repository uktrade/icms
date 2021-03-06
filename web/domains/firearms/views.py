import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import F
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from web.domains.file.views import handle_uploaded_file
from web.domains.importer.models import Importer
from web.views import ModelFilterView
from web.views.actions import Archive, Edit, Unarchive
from web.views.mixins import PostActionMixin

from .forms import (
    FirearmsAuthorityForm,
    FirearmsQuantityForm,
    ObsoleteCalibreForm,
    ObsoleteCalibreGroupFilter,
    ObsoleteCalibreGroupForm,
)
from .models import (
    ActQuantity,
    FirearmsAct,
    FirearmsAuthority,
    ObsoleteCalibre,
    ObsoleteCalibreGroup,
)

logger = logging.getLogger(__name__)


class ObsoleteCalibreListView(PostActionMixin, ModelFilterView):
    template_name = "web/domains/firearms/group/list.html"
    filterset_class = ObsoleteCalibreGroupFilter
    model = ObsoleteCalibreGroup
    page_title = "Maintain Obsolete Calibres"
    permission_required = "web.reference_data_access"
    paginate = False

    class Display:
        fields = ["name", "calibres__count"]
        fields_config = {
            "name": {"header": "Obsolete Calibre Group Name", "link": True},
            "calibres__count": {
                "header": "Number of Items",
                "tooltip": "The total number of obsolete calibres in this group",
            },
        }
        actions = [Edit(), Archive(), Unarchive()]


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_obsolete_calibre_group(request):
    if request.POST:
        form = ObsoleteCalibreGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            last_group = ObsoleteCalibreGroup.objects.order_by("-order").first()
            if last_group:
                order = last_group.order + 1
            else:
                order = 1
            group.order = order
            group.save()

            return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": group.pk}))
    else:
        form = ObsoleteCalibreGroupForm()

    context = {"form": form}

    return render(request, "web/domains/firearms/group/create.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=pk)

    if request.POST:
        form = ObsoleteCalibreGroupForm(request.POST, instance=calibre_group)
        if form.is_valid():
            form.save()
            return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": pk}))
    else:
        form = ObsoleteCalibreGroupForm(instance=calibre_group)

    context = {
        "form": form,
        "object": calibre_group,
        "display_archived": request.GET.get("display_archived"),
    }

    return render(request, "web/domains/firearms/group/edit.html", context)


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def order_obsolete_calibre_group(request):
    with transaction.atomic():
        for order, pk in enumerate(request.POST.getlist("order[]")):
            calibre_group = ObsoleteCalibreGroup.objects.get(pk=pk)
            calibre_group.order = order
            calibre_group.save()

    return redirect(reverse("obsolete-calibre-group-list"))


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def archive_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup.objects.filter(is_active=True), pk=pk)
    calibre_group.is_active = False
    calibre_group.save()

    return redirect(reverse("obsolete-calibre-group-list"))


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def unarchive_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup.objects.filter(is_active=False), pk=pk)
    calibre_group.is_active = True
    calibre_group.save()

    return redirect(reverse("obsolete-calibre-group-list"))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_obsolete_calibre(request, calibre_group_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    if request.POST:
        form = ObsoleteCalibreForm(request.POST)
        if form.is_valid():
            calibre = form.save(commit=False)
            calibre.calibre_group = calibre_group
            last_calibre = ObsoleteCalibre.objects.order_by("-order").first()
            if last_calibre:
                order = last_calibre.order + 1
            else:
                order = 1
            calibre.order = order
            calibre.save()

            return redirect(
                reverse(
                    "obsolete-calibre-edit",
                    kwargs={"calibre_group_pk": calibre_group_pk, "calibre_pk": calibre.pk},
                )
            )
    else:
        form = ObsoleteCalibreForm()

    context = {"form": form, "object": calibre_group}

    return render(request, "web/domains/firearms/create.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_obsolete_calibre(request, calibre_group_pk, calibre_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    calibre = get_object_or_404(calibre_group.calibres, pk=calibre_pk)

    if request.POST:
        form = ObsoleteCalibreForm(request.POST, instance=calibre)
        if form.is_valid():
            form.save()
            return redirect(
                reverse(
                    "obsolete-calibre-edit",
                    kwargs={"calibre_group_pk": calibre_group_pk, "calibre_pk": calibre_pk},
                )
            )
    else:
        form = ObsoleteCalibreForm(instance=calibre)

    context = {"form": form, "object": calibre_group}

    return render(request, "web/domains/firearms/edit.html", context)


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def order_obsolete_calibre(request, calibre_group_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)

    with transaction.atomic():
        for order, pk in enumerate(request.POST.getlist("order[]")):
            calibre = calibre_group.calibres.get(pk=pk)
            calibre.order = order
            calibre.save()

    return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": calibre_group_pk}))


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def archive_obsolete_calibre(request, calibre_group_pk, calibre_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    calibre = get_object_or_404(calibre_group.calibres.filter(is_active=True), pk=calibre_pk)

    calibre.is_active = False
    calibre.save()

    return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": calibre_group_pk}))


@require_POST
@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def unarchive_obsolete_calibre(request, calibre_group_pk, calibre_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    calibre = get_object_or_404(calibre_group.calibres.filter(is_active=False), pk=calibre_pk)

    calibre.is_active = True
    calibre.save()

    return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": calibre_group_pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def view_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=pk)

    return render(request, "web/domains/firearms/group/view.html", {"object": calibre_group})


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def create_firearms_authorities(request, pk):
    importer = get_object_or_404(Importer, pk=pk)

    if request.POST:
        form = FirearmsAuthorityForm(importer, request.POST, request.FILES)
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority, ActQuantity, extra=0, form=FirearmsQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST)

        if form.is_valid() and clause_quantity_formset.is_valid():
            firearms_authority = form.save()
            for clause_quantity_form in clause_quantity_formset:
                clause_quantity = clause_quantity_form.save(commit=False)
                clause_quantity.firearmsauthority = firearms_authority
                clause_quantity.save()

            files = request.FILES.getlist("files")
            for f in files:
                handle_uploaded_file(f, request.user, firearms_authority.files)

            return redirect(
                reverse(
                    "importer-firearms-authorities-edit",
                    kwargs={
                        "importer_pk": importer.pk,
                        "firearms_authority_pk": firearms_authority.pk,
                    },
                )
            )
    else:
        form = FirearmsAuthorityForm(importer)

        # Create a formset to specify quantity for each firearmsacts
        initial = FirearmsAct.objects.annotate(firearmsact=F("pk")).values("firearmsact")
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority,
            ActQuantity,
            extra=len(initial),
            form=FirearmsQuantityForm,
            can_delete=False,
        )
        clause_quantity_formset = ClauseQuantityFormSet(initial=initial)

    context = {
        "object": importer,
        "form": form,
        "formset": clause_quantity_formset,
    }

    return render(request, "web/domains/importer/create-firearms-authority.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_firearms_authorities(request, importer_pk, firearms_authority_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    firearms_authority = get_object_or_404(FirearmsAuthority, pk=firearms_authority_pk)

    if request.POST:
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority, ActQuantity, extra=0, form=FirearmsQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST, instance=firearms_authority)

        form = FirearmsAuthorityForm(
            importer, request.POST, request.FILES, instance=firearms_authority
        )
        if form.is_valid() and clause_quantity_formset.is_valid():
            firearms_authority = form.save()
            clause_quantity_formset.save()

            files = request.FILES.getlist("files")
            for f in files:
                handle_uploaded_file(f, request.user, firearms_authority.files)

            return redirect(
                reverse(
                    "importer-firearms-authorities-edit",
                    kwargs={
                        "importer_pk": importer.pk,
                        "firearms_authority_pk": firearms_authority.pk,
                    },
                )
            )
    else:
        form = FirearmsAuthorityForm(importer, instance=firearms_authority)
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority, ActQuantity, extra=0, form=FirearmsQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(instance=firearms_authority)

    context = {
        "object": importer,
        "form": form,
        "firearms_authority": firearms_authority,
        "formset": clause_quantity_formset,
    }

    return render(request, "web/domains/importer/edit-firearms-authority.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def detail_firearms_authorities(request, importer_pk, firearms_authority_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    firearms_authority = get_object_or_404(FirearmsAuthority, pk=firearms_authority_pk)

    context = {
        "object": importer,
        "firearms_authority": firearms_authority,
    }

    return render(request, "web/domains/importer/detail-firearms-authority.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_firearms_authorities(request, importer_pk, firearms_authority_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    authority = get_object_or_404(
        importer.firearms_authorities.filter(is_active=True), pk=firearms_authority_pk
    )
    authority.is_active = False
    authority.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def unarchive_firearms_authorities(request, importer_pk, firearms_authority_pk):
    importer = get_object_or_404(Importer, pk=importer_pk)
    authority = get_object_or_404(
        importer.firearms_authorities.filter(is_active=False), pk=firearms_authority_pk
    )
    authority.is_active = True
    authority.save()

    return redirect(reverse("importer-edit", kwargs={"pk": importer.pk}))


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_file_firearms_authorities(request, importer_pk, firearms_authority_pk, file_pk):
    authority = get_object_or_404(
        FirearmsAuthority, pk=firearms_authority_pk, importer_id=importer_pk
    )
    document = authority.files.get(pk=file_pk)
    document.is_active = False
    document.save()

    return redirect(
        reverse(
            "importer-firearms-authorities-edit",
            kwargs={"importer_pk": importer_pk, "firearms_authority_pk": firearms_authority_pk},
        )
    )
