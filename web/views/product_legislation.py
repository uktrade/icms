from django.urls import reverse_lazy
from django.views.generic.edit import (CreateView, UpdateView)
from web.base.forms import FilterSet, ModelForm, widgets
from web.base.views import (FilteredListView)
from web.models import ProductLegislation
from django_filters import (CharFilter, ChoiceFilter, BooleanFilter)


class ProductLegislationFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='icontains',
        widget=widgets.TextInput,
        label='Legislation Name')

    is_biocidal = ChoiceFilter(
        field_name='is_biocidal',
        choices=((True, 'Yes'), (False, 'No')),
        lookup_expr='exact',
        label='Is Biocidal')

    is_biocidal_claim = ChoiceFilter(
        field_name='is_biocidal_claim',
        choices=((True, 'Yes'), (False, 'No')),
        lookup_expr='exact',
        label='Is Biocidal Claim')

    is_eu_cosmetics_regulation = ChoiceFilter(
        field_name='is_eu_cosmetics_regulation',
        choices=((True, 'Yes'), (False, 'No')),
        lookup_expr='exact',
        label='Is EU Cosmetics Regulation')

    status = ChoiceFilter(
        field_name='is_active',
        choices=((True, 'Current'), (False, 'Archived')),
        lookup_expr='exact',
        label='Status')

    class Meta:
        fields = []
        model = ProductLegislation
        config = {
            'label': {
                'cols': 'twelve',
                'optional_indicators': False,
                'prompt': 'north'
            },
            'input': {'cols': 'twelve'},
            'padding': None,
            'actions': {
                'padding': None,
                'submit': {
                    'name': '',
                    'value': '',
                    'label': 'Apply Filter'
                },
                'link': {
                    'label': 'Clear Filter',
                    'href': 'product-legislation-list'
                }
            }
        }


class ProductLegislationEditForm(ModelForm):
    class Meta:
        model = ProductLegislation
        fields = ['name', 'is_biocidal', 'is_biocidal_claim',
                  'is_eu_cosmetics_regulation']
        labels = {
            'name': 'Legislation Name',
            'is_biocidal': 'Biocidal',
            'is_biocidal_claim': 'Biocidal Claim',
            'is_eu_cosmetics_regulation': 'EU Cosmetics Regulation'
        }
        help_texts = {
            'is_biocidal': 'Product type numbers and active ingredients must be \
                entered by the applicant when biocidal legislation is selected',
            'is_eu_cosmetics_regulation': "A 'responsible person' statement \
            may be added to the issued certificate schedule when the applicant \
            selects EU Cosmetics Regulation legislation"
        }
        config = {
            'label': {
                'cols': 'three',
                'optional_indicators': False
            },
            'input': {
                'cols': 'six'
            },
            'padding': {
                'right': 'three'
            },
            'actions': {
                'padding': {
                    'left': 'three'
                },
                'link': {
                    'label': 'Cancel',
                    'href': 'constabulary-list'
                }
            }
        }


class ProductLegislationCreateForm(ModelForm):
    class Meta(ProductLegislationEditForm.Meta):
        pass


class ProductLegislationListView(FilteredListView):
    template_name = 'web/product-legislation/list.html'
    filterset_class = ProductLegislationFilter
    paginate_by = 100
    load_immediate = True   # show all results on first page load


class ProductLegislationEditView(UpdateView):
    template_name = 'web/product-legislation/edit.html'
    form_class = ProductLegislationEditForm
    model = ProductLegislation
    success_url = reverse_lazy('product-legislation-list')


class ProductLegislationCreateView(CreateView):
    template_name = 'web/product-legislation/edit.html'
    form_class = ProductLegislationCreateForm
    model = ProductLegislation
    success_url = reverse_lazy('product-legislation-list')
