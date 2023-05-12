import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from web.domains.case.forms import DocumentForm
from web.domains.file.utils import create_file_model
from web.models import Importer
from web.permissions import Perms, can_user_edit_firearm_authorities
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3
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
    permission_required = Perms.sys.ilb_admin
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def create_obsolete_calibre_group(request):
    if request.method == "POST":
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=pk)

    if request.method == "POST":
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def order_obsolete_calibre_group(request):
    with transaction.atomic():
        for order, pk in enumerate(request.POST.getlist("order[]")):
            calibre_group = ObsoleteCalibreGroup.objects.get(pk=pk)
            calibre_group.order = order
            calibre_group.save()

    return redirect(reverse("obsolete-calibre-group-list"))


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def archive_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup.objects.filter(is_active=True), pk=pk)
    calibre_group.is_active = False
    calibre_group.save()

    return redirect(reverse("obsolete-calibre-group-list"))


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def unarchive_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup.objects.filter(is_active=False), pk=pk)
    calibre_group.is_active = True
    calibre_group.save()

    return redirect(reverse("obsolete-calibre-group-list"))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def create_obsolete_calibre(request, calibre_group_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    if request.method == "POST":
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_obsolete_calibre(request, calibre_group_pk, calibre_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    calibre = get_object_or_404(calibre_group.calibres, pk=calibre_pk)

    if request.method == "POST":
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
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
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def archive_obsolete_calibre(request, calibre_group_pk, calibre_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    calibre = get_object_or_404(calibre_group.calibres.filter(is_active=True), pk=calibre_pk)

    calibre.is_active = False
    calibre.save()

    return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": calibre_group_pk}))


@require_POST
@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def unarchive_obsolete_calibre(request, calibre_group_pk, calibre_pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=calibre_group_pk)
    calibre = get_object_or_404(calibre_group.calibres.filter(is_active=False), pk=calibre_pk)

    calibre.is_active = True
    calibre.save()

    return redirect(reverse("obsolete-calibre-group-edit", kwargs={"pk": calibre_group_pk}))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def view_obsolete_calibre_group(request, pk):
    calibre_group = get_object_or_404(ObsoleteCalibreGroup, pk=pk)

    return render(request, "web/domains/firearms/group/view.html", {"object": calibre_group})


@login_required
def create_firearms(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    importer: Importer = get_object_or_404(Importer, pk=pk)

    if request.method == "POST":
        form = FirearmsAuthorityForm(importer, request.POST, request.FILES)
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority, ActQuantity, extra=0, form=FirearmsQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST)

        if form.is_valid() and clause_quantity_formset.is_valid():
            firearms = form.save()

            for clause_quantity_form in clause_quantity_formset:
                clause_quantity = clause_quantity_form.save(commit=False)
                clause_quantity.firearmsauthority = firearms
                clause_quantity.save()

            return redirect(reverse("importer-firearms-edit", kwargs={"pk": firearms.pk}))
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
def edit_firearms(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(FirearmsAuthority, pk=pk)

    if request.method == "POST":
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority, ActQuantity, extra=0, form=FirearmsQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(request.POST, instance=firearms)

        form = FirearmsAuthorityForm(
            firearms.importer, request.POST, request.FILES, instance=firearms
        )

        if form.is_valid() and clause_quantity_formset.is_valid():
            firearms = form.save()
            clause_quantity_formset.save()

            return redirect(reverse("importer-firearms-edit", kwargs={"pk": firearms.pk}))
    else:
        form = FirearmsAuthorityForm(firearms.importer, instance=firearms)
        ClauseQuantityFormSet = inlineformset_factory(
            FirearmsAuthority, ActQuantity, extra=0, form=FirearmsQuantityForm, can_delete=False
        )
        clause_quantity_formset = ClauseQuantityFormSet(instance=firearms)

    context = {
        "object": firearms.importer,
        "form": form,
        "firearms_authority": firearms,
        "formset": clause_quantity_formset,
    }

    return render(request, "web/domains/importer/edit-firearms-authority.html", context)


@login_required
def view_firearms(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(FirearmsAuthority, pk=pk)

    context = {
        "object": firearms.importer,
        "firearms_authority": firearms,
    }

    return render(request, "web/domains/importer/detail-firearms-authority.html", context)


@login_required
@require_POST
def archive_firearms(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(
        FirearmsAuthority.objects.filter(is_active=True), pk=pk
    )
    firearms.is_active = False
    firearms.save()

    return redirect(reverse("importer-edit", kwargs={"pk": firearms.importer.pk}))


@login_required
@require_POST
def unarchive_firearms(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(
        FirearmsAuthority.objects.filter(is_active=False), pk=pk
    )
    firearms.is_active = True
    firearms.save()

    return redirect(reverse("importer-edit", kwargs={"pk": firearms.importer.pk}))


@login_required
def add_document_firearms(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(FirearmsAuthority, pk=pk)

    if request.method == "POST":
        form = DocumentForm(data=request.POST, files=request.FILES)

        if form.is_valid():
            document = form.cleaned_data.get("document")
            create_file_model(document, request.user, firearms.files)

            return redirect(reverse("importer-firearms-edit", kwargs={"pk": pk}))
    else:
        form = DocumentForm()

    context = {
        "importer": firearms.importer,
        "form": form,
        "firearms": firearms,
    }

    return render(request, "web/domains/importer/add-document-firearms.html", context)


@login_required
def view_document_firearms(
    request: AuthenticatedHttpRequest, firearms_pk: int, document_pk: int
) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(FirearmsAuthority, pk=firearms_pk)

    document = firearms.files.get(pk=document_pk)
    file_content = get_file_from_s3(document.path)

    response = HttpResponse(content=file_content, content_type=document.content_type)
    response["Content-Disposition"] = f'attachment; filename="{document.filename}"'

    return response


@login_required
@require_POST
def delete_document_firearms(
    request: AuthenticatedHttpRequest, firearms_pk: int, document_pk: int
) -> HttpResponse:
    if not can_user_edit_firearm_authorities(request.user):
        raise PermissionDenied

    firearms: FirearmsAuthority = get_object_or_404(FirearmsAuthority, pk=firearms_pk)

    document = firearms.files.get(pk=document_pk)
    document.is_active = False
    document.save()

    return redirect(reverse("importer-firearms-edit", kwargs={"pk": firearms_pk}))
