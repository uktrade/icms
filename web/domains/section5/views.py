from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from web.domains.section5.filters import Section5Filter
from web.domains.section5.forms import Section5ClauseForm
from web.models import Section5Clause
from web.permissions import Perms
from web.views import ModelFilterView
from web.views.actions import Archive, Edit, Unarchive


class EditSection5Action(Edit):
    def href(self, obj):
        return reverse("section5:edit", kwargs={"pk": obj.pk})


class ListSection5(ModelFilterView):
    template_name = "web/domains/section5/list.html"
    filterset_class = Section5Filter
    model = Section5Clause
    permission_required = Perms.sys.ilb_admin
    page_title = "Maintain Section 5 Clauses"
    ordering = ("clause",)

    def get_initial_data(self, queryset: QuerySet) -> QuerySet:
        return queryset

    class Display:
        fields = ["clause", "description"]
        fields_config = {
            "clause": {"header": "Clause"},
            "description": {"header": "Description"},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [
            EditSection5Action(hide_if_archived_object=True, **opts),
            Archive(**opts),
            Unarchive(**opts),
        ]


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def create_section5(request):
    if request.method == "POST":
        form = Section5ClauseForm(request.POST)
        if form.is_valid():
            clause = form.save(commit=False)
            clause.created_by = request.user
            clause.save()
            messages.success(request, "Section 5 clause created successfully.")
            return redirect(reverse("section5:edit", kwargs={"pk": clause.pk}))
    else:
        form = Section5ClauseForm()

    return render(request, "web/domains/section5/create.html", {"form": form})


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_section5(request, pk):
    clause = get_object_or_404(Section5Clause, pk=pk)

    if request.method == "POST":
        form = Section5ClauseForm(request.POST, instance=clause)
        if form.is_valid():
            clause = form.save(commit=False)
            clause.updated_by = request.user
            clause.save()
            return redirect(reverse("section5:edit", kwargs={"pk": pk}))
    else:
        form = Section5ClauseForm(instance=clause)

    context = {"object": clause, "form": form}
    return render(request, "web/domains/section5/edit.html", context)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def archive_section5(request, pk):
    clause = get_object_or_404(Section5Clause.objects.filter(is_active=True), pk=pk)
    clause.is_active = False
    clause.save()

    return redirect(reverse("section5:list"))


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def unarchive_section5(request, pk):
    clause = get_object_or_404(Section5Clause.objects.filter(is_active=False), pk=pk)
    clause.is_active = True
    clause.save()

    return redirect(reverse("section5:list"))
