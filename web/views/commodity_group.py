from django.urls import reverse_lazy
from django.views.generic.edit import (UpdateView, CreateView)
from django_filters import (CharFilter, ChoiceFilter, ModelChoiceFilter,
                            BooleanFilter)
from web.base.forms import FilterSet, widgets, ModelForm
from web.base.forms.fields import (DisplayField, CharField)
from web.base.forms.widgets import Textarea
from web.base.views import FilteredListView
from web.models import (CommodityGroup, Commodity, Unit)
from .filters import _filter_config


class CommodityGroupFilter(FilterSet):
    group_type = ChoiceFilter(
        field_name='group_type',
        choices=CommodityGroup.TYPES,
        label='Group Type')
    commodity_types = ChoiceFilter(
        field_name='commodity_type',
        choices=Commodity.TYPES,
        label='Commodity Types')

    group_code = CharFilter(
        field_name='group_code', lookup_expr='icontains', label='Group Code')
    group_name = CharFilter(
        field_name='group_name', lookup_expr='icontains', label='Group Name')
    group_description = CharFilter(
        field_name='group_description',
        lookup_expr='icontains',
        label='Group Description')
    commodity_code = CharFilter(
        field_name='commodities__commodity_code',
        lookup_expr='icontains',
        label='Commodity Code')
    unit = ModelChoiceFilter(queryset=Unit.objects.all())

    is_archived = BooleanFilter(
        field_name='is_active',
        widget=widgets.CheckboxInput,
        lookup_expr='exact',
        exclude=True,
        label='Search Archived')

    class Meta:
        model = CommodityGroup
        fields = []
        config = _filter_config


class CommodityGroupEditForm(ModelForm):
    group_type = DisplayField(
        label='Group Type',
        help_text='Auto groups will include all commodities beginning with the \
            Group Code. Category groups will allow you manually include \
            commodities')
    commodity_type = DisplayField(
        label='Commodity Types',
        help_text='Please choose what type of commodities this group should \
        contain')

    class Meta:
        model = CommodityGroup
        fields = [
            'group_type', 'commodity_type', 'group_code', 'group_description'
        ]
        labels = {
            'commodity_type': 'Commodity Types',
            'group_code': 'Group Code',
            'group_description': 'Group Description'
        }
        help_texts = {
            'group_code':
            'For Auto Groups: please enter the first four digits \
            of the commodity code you want to include in this group.\
            For Caegory Groups: enter the code that will identify this \
            category. This can be override by the Group Name below.'
        }
        widgets = {
            'group_description': Textarea(attrs={
                'rows': 5,
                'cols': 20
            })
        }
        config = {
            'label': {
                'cols': 'three'
            },
            'input': {
                'cols': 'six'
            },
            'padding': {
                'right': 'three'
            },
            'actions': {
                'padding': {
                    'left': None
                },
                'link': {
                    'label': 'Cancel',
                    'href': 'commodity-groups'
                },
                'submit': {
                    'label': 'Save'
                }
            }
        }


class CommodityGroupCreateForm(ModelForm):
    group_type = CharField(
        widget=widgets.Select(choices=CommodityGroup.TYPES),
        help_text='Auto groups will include all commodities beginning with the \
            Group Code. Category groups will allow you manually include \
            commodities')

    commodity_type = CharField(
        widget=widgets.Select(choices=Commodity.TYPES),
        label='Commodity Types',
        help_text='Please choose what type of commodities this group should \
        contain')

    class Meta(CommodityGroupEditForm.Meta):
        pass


class CommodityGroupEditView(UpdateView):
    template_name = 'web/commodity-group/edit.html'
    form_class = CommodityGroupEditForm
    model = CommodityGroup
    success_url = reverse_lazy('commodity-groups')


class CommodityGroupCreateView(CreateView):
    template_name = 'web/commodity-group/create.html'
    form_class = CommodityGroupCreateForm
    model = CommodityGroup
    success_url = reverse_lazy('commodity-groups')


class CommodityGroupListView(FilteredListView):
    template_name = 'web/commodity-group/list.html'
    filterset_class = CommodityGroupFilter
