from django.urls import reverse_lazy
from web.views import ModelCreateView, ModelFilterView, ModelUpdateView

from .forms import (CommodityEditForm, CommodityFilter, CommodityForm,
                    CommodityGroupEditForm, CommodityGroupFilter,
                    CommodityGroupForm)
from .models import Commodity, CommodityGroup


class CommodityListView(ModelFilterView):
    template_name = 'web/commodity/list.html'
    filterset_class = CommodityFilter
    model = Commodity

    class Display:
        fields = [
            'commodity_code', 'commodity_type_verbose',
            ('validity_start_date', 'validity_end_date')
        ]
        headers = ['Commodity Code', 'Commodity Type', 'Validity']
        view = False
        edit = True
        archive = True


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

    class Display:
        fields = [
            'group_type_verbose', 'commodity_type_verbose', 'group_code',
            'group_description'
        ]
        headers = [
            'Commodity Code', 'Commodity Type', 'Group Code/ Group Name',
            'Descripption/ Commodities'
        ]
        view = False
        edit = True
        archive = True


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
