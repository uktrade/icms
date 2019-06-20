from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView
from web.base.forms import ModelForm
from web.models import Team, Country


class CountryEditForm(ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'type']
        labels = {
            'validity_start_date': 'First day of validity',
            'validity_end_date': 'Last day of validity',
            'sigl_product_type': 'SIGL Product Type'
        }
        help_texts = {
            'name':
            'The commodity code will be available for applications to choose \
            on applications forms, starting on this date',
            'type':
            'After this date, the commodity will no \
            longer be available for applications to choose on application \
            Textile commodities'
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
                    'href': 'commodity-list'
                },
                'submit': {
                    'label': 'Save'
                }
            }
        }


class CountryCreateForm(ModelForm):
    class Meta:
        model = Country
        fields = ['name']
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
                    'href': 'country-list'
                },
                'submit': {
                    'label': 'Create'
                }
            }
        }


class CountryGroupView(ListView):
    model = Team
    template_name = 'web/country-group/view.html'


class CountryListView(ListView):
    model = Team
    template_name = 'web/country/list.html'


class CountryEditView(UpdateView):
    model = Country
    template_name = 'web/country/edit.html'
    form_class = CountryEditForm
    success_url = reverse_lazy('country-list')


class CountryCreateView(CreateView):
    # model = Country
    template_name = 'web/country/create.html'
    form_class = CountryCreateForm
    success_url = reverse_lazy('country-list')


class CountryTranslationListView(ListView):
    model = Team
    template_name = 'web/country/translations/list.html'
