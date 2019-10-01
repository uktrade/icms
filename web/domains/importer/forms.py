from django.forms.fields import ChoiceField
from django_filters import CharFilter
from web.forms import ModelEditForm, ModelSearchFilter
from web.forms.mixins import ReadonlyFormMixin

from .models import Importer


class ImporterFilter(ModelSearchFilter):
    importer_entity_type = CharFilter(field_name='type',
                                      lookup_expr='icontains',
                                      label='Importer Entity Type')

    importer_name = CharFilter(lookup_expr='icontains',
                               label='Importer Name',
                               method='filter_importer_name')

    # Filter base queryset to only get importers that are not agents.
    @property
    def qs(self):
        queryset = super().qs
        return queryset.filter(main_importer__isnull=True)

    def filter_importer_name(self, queryset, name, value):
        if not value:
            return queryset

        #  Filter concatanation of title name and last name in case the importer
        #  to cover both individual importers and organisations
        # see manager.py for annotated queryset to filter in concatanated
        return queryset.filter(full_name__icontains=value)

    #  valid_end = DateFilter(field_name='validity_end_date',
    #  widget=widgets.DateInput,
    #  lookup_expr='lte',
    #  label='and')

    #  is_archived = BooleanFilter(field_name='is_active',
    #  widget=widgets.CheckboxInput,
    #  lookup_expr='exact',
    #  exclude=True,
    #  label='Search Archived')
    #

    class Meta:
        model = Importer
        fields = []


class ImporterEditForm(ModelEditForm):
    type = ChoiceField(choices=Importer.TYPES)

    class Meta:
        model = Importer
        fields = ['type', 'name', 'region_origin', 'comments']
        labels = {'type': 'Entity Type'}


class ImporterDisplayForm(ReadonlyFormMixin, ImporterEditForm):
    pass
