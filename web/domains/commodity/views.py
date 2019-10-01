from django.urls import reverse_lazy
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import (CommodityEditForm, CommodityFilter, CommodityForm,
                    CommodityGroupFilter, CommodityGroupForm,
                    CommodityGroupEditForm)
from .models import Commodity, CommodityGroup


class CommodityListView(ModelFilterView):
    template_name = 'web/commodity/list.html'
    filterset_class = CommodityFilter
    model = Commodity
    config = {'title': 'Maintain Commodities'}


class CommodityEditView(ModelUpdateView):
    template_name = 'web/commodity/edit.html'
    form_class = CommodityEditForm
    model = Commodity
    success_url = reverse_lazy('commodity-list')
    config = {'title': 'Edit Commodity'}


class CommodityCreateView(ModelCreateView):
    template_name = 'web/commodity/create.html'
    form_class = CommodityForm
    success_url = reverse_lazy('commodity-list')
    config = {'title': 'New Commodity'}


class CommodityGroupListView(ModelFilterView):
    template_name = 'web/commodity-group/list.html'
    filterset_class = CommodityGroupFilter
    model = CommodityGroup
    config = {'title': 'Maintain Commodity Groups'}


class CommodityGroupEditView(ModelUpdateView):
    template_name = 'web/commodity-group/edit.html'
    form_class = CommodityGroupEditForm
    model = CommodityGroup
    success_url = reverse_lazy('commodity-group-list')
    config = {'title': 'Edit Commodity Group'}


class CommodityGroupCreateView(ModelCreateView):
    template_name = 'web/commodity-group/edit.html'
    form_class = CommodityGroupForm
    model = CommodityGroup
    success_url = reverse_lazy('commodity-group-list')
    config = {'title': 'New Commodity Group'}
