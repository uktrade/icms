from web.views import ModelFilterView

from .models import Template
from .forms import TemplatesFilter


class TemplateListView(ModelFilterView):
    template_name = 'web/template/list.html'
    filterset_class = TemplatesFilter
    model = Template
    config = {'title': 'Maintain Templates'}
