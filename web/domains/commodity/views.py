from django.urls import reverse_lazy

from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, Edit, Unarchive

from .forms import (
    CommodityEditForm,
    CommodityFilter,
    CommodityForm,
    CommodityGroupEditForm,
    CommodityGroupFilter,
    CommodityGroupForm,
)
from .models import Commodity, CommodityGroup


class CommodityListView(ModelFilterView):
    template_name = "web/domains/commodity/list.html"
    filterset_class = CommodityFilter
    model = Commodity
    permission_required = "web.reference_data_access"
    page_title = "Maintain Commodities"

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
    permission_required = "web.reference_data_access"


class CommodityCreateView(ModelCreateView):
    template_name = "web/domains/commodity/create.html"
    form_class = CommodityForm
    success_url = reverse_lazy("commodity-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"
    page_title = "New Commodity"


class CommodityDetailView(ModelDetailView):
    form_class = CommodityForm
    model = Commodity
    permission_required = "web.reference_data_access"
    cancel_url = reverse_lazy("commodity-list")


class CommodityGroupListView(ModelFilterView):
    template_name = "web/domains/commodity/group/list.html"
    filterset_class = CommodityGroupFilter
    model = CommodityGroup
    permission_required = "web.reference_data_access"

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
    permission_required = "web.reference_data_access"


class CommodityGroupCreateView(ModelCreateView):
    template_name = "web/domains/commodity/group/create.html"
    form_class = CommodityGroupForm
    model = CommodityGroup
    success_url = reverse_lazy("commodity-group-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"


class CommodityGroupDetailView(ModelDetailView):
    form_class = CommodityGroupForm
    model = CommodityGroup
    permission_required = "web.reference_data_access"
    cancel_url = reverse_lazy("commodity-group-list")
