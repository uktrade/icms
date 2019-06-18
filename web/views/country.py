from django.views.generic.list import ListView
from web.models import Team


class CountryGroupView(ListView):
    model = Team
    template_name = 'web/country-group/view.html'


class CountryListView(ListView):
    model = Team
    template_name = 'web/country/list.html'
