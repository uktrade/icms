from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from web.permissions import Perms
from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, Edit, Unarchive

from .forms import (
    CommodityEditForm,
    CommodityFilter,
    CommodityForm,
    CommodityGroupEditForm,
    CommodityGroupFilter,
    CommodityGroupForm,
    UsageForm,
)
from .models import Commodity, CommodityGroup, Usage

if TYPE_CHECKING:
    from django.db.models import QuerySet


class CommodityListView(ModelFilterView):
    template_name = "web/domains/commodity/list.html"
    filterset_class = CommodityFilter
    model = Commodity
    permission_required = Perms.sys.commodity_admin
    page_title = "Maintain Commodities"

    def get_queryset(self):
        qs = super().get_queryset()

        return qs.select_related("commodity_type")

    class Display:
        fields = ["commodity_code", "commodity_type", ("validity_start_date", "validity_end_date")]
        fields_config = {
            "commodity_code": {"header": "Commodity Code", "link": True},
            "commodity_type": {"header": "Commodity Type"},
            "validity_start_date": {"header": "Validity Start Date"},
            "validity_end_date": {"header": "Validity End Date"},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [Edit(**opts), Archive(**opts), Unarchive(**opts)]


class CommodityEditView(ModelUpdateView):
    template_name = "web/domains/commodity/edit.html"
    form_class = CommodityEditForm
    model = Commodity
    success_url = reverse_lazy("commodity-list")
    cancel_url = success_url
    permission_required = Perms.sys.commodity_admin


class CommodityCreateView(ModelCreateView):
    template_name = "web/domains/commodity/create.html"
    form_class = CommodityForm
    success_url = reverse_lazy("commodity-list")
    cancel_url = success_url
    permission_required = Perms.sys.commodity_admin
    page_title = "New Commodity"


class CommodityDetailView(ModelDetailView):
    form_class = CommodityForm
    model = Commodity
    permission_required = Perms.sys.commodity_admin
    cancel_url = reverse_lazy("commodity-list")


class CommodityGroupListView(ModelFilterView):
    template_name = "web/domains/commodity/group/list.html"
    filterset_class = CommodityGroupFilter
    model = CommodityGroup
    permission_required = Perms.sys.commodity_admin

    def get_queryset(self):
        qs = super().get_queryset()

        return qs.select_related("commodity_type").prefetch_related("commodities")

    class Display:
        fields = [
            "group_type_verbose",
            "commodity_type_verbose",
            ("group_code", "group_name"),
            ("group_description", "commodities"),
        ]
        fields_config = {
            "group_type_verbose": {"header": "Group Type"},
            "commodity_type_verbose": {"header": "Commodity Type"},
            "group_code": {"header": "Group Code"},
            "group_name": {"header": "Group Name"},
            "group_description": {"header": "Description"},
            "commodities": {"header": "Commodities", "show_all": True, "separator": ","},
        }
        opts = {"inline": True, "icon_only": True}
        actions = [Edit(**opts), Archive(**opts), Unarchive(**opts)]


class CommodityGroupEditView(ModelUpdateView):
    template_name = "web/domains/commodity/group/edit.html"
    form_class = CommodityGroupEditForm
    model = CommodityGroup
    success_url = reverse_lazy("commodity-group-list")
    cancel_url = success_url
    permission_required = Perms.sys.commodity_admin

    def get_queryset(self) -> "QuerySet[CommodityGroup]":
        qs: "QuerySet[CommodityGroup]" = super().get_queryset()

        return qs.prefetch_related("usages__country", "usages__application_type")


class CommodityGroupCreateView(ModelCreateView):
    template_name = "web/domains/commodity/group/create.html"
    form_class = CommodityGroupForm
    model = CommodityGroup
    permission_required = Perms.sys.commodity_admin

    def get_success_url(self):
        return reverse("commodity-group-edit", kwargs={"pk": self.object.pk})


class CommodityGroupDetailView(ModelDetailView):
    form_class = CommodityGroupForm
    model = CommodityGroup
    permission_required = Perms.sys.commodity_admin
    cancel_url = reverse_lazy("commodity-group-list")


@login_required
@permission_required(Perms.sys.commodity_admin, raise_exception=True)
def add_usage(request, pk):
    commodity_group = get_object_or_404(CommodityGroup, pk=pk)

    if request.method == "POST":
        form = UsageForm(request.POST, initial={"commodity_group": pk})
        if form.is_valid():
            usage = form.save()
            return redirect(
                reverse(
                    "commodity-group-usage-edit",
                    kwargs={"commodity_group_pk": pk, "usage_pk": usage.pk},
                )
            )
    else:
        form = UsageForm(initial={"commodity_group": pk})

    context = {
        "object": commodity_group,
        "form": form,
    }
    return render(request, "web/domains/commodity/group/create-usage.html", context)


@login_required
@permission_required(Perms.sys.commodity_admin, raise_exception=True)
def edit_usage(request, commodity_group_pk, usage_pk):
    commodity_group = get_object_or_404(CommodityGroup, pk=commodity_group_pk)
    usage = get_object_or_404(Usage, pk=usage_pk)

    if request.method == "POST":
        form = UsageForm(request.POST, instance=usage)
        if form.is_valid():
            form.save()
            return redirect(
                reverse(
                    "commodity-group-usage-edit",
                    kwargs={"commodity_group_pk": commodity_group_pk, "usage_pk": usage_pk},
                )
            )
    else:
        form = UsageForm(instance=usage)

    context = {
        "object": commodity_group,
        "form": form,
        "usage_pk": usage_pk,
    }
    return render(request, "web/domains/commodity/group/edit-usage.html", context)


@login_required
@permission_required(Perms.sys.commodity_admin, raise_exception=True)
@require_POST
def delete_usage(request, commodity_group_pk, usage_pk):
    get_object_or_404(CommodityGroup, pk=commodity_group_pk)
    usage = get_object_or_404(Usage, pk=usage_pk)
    usage.delete()

    return redirect(reverse("commodity-group-edit", kwargs={"pk": commodity_group_pk}))
