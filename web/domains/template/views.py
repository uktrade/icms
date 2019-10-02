from web.views import ModelFilterView

from .models import Template
from .forms import TemplatesFilter


class TemplateListView(ModelFilterView):
    template_name = 'web/template/list.html'
    filterset_class = TemplatesFilter
    model = Template
    config = {'title': 'Maintain Templates'}

    # Default display fields on the listing page of the model
    class Display:
        fields = [
            'template_name', 'application_domain_verbose',
            'template_type_verbose', 'template_status'
        ]
        headers = [
            'Template Name', 'Application Domain', 'Template Type',
            'Template Status'
        ]
        #  Display actions
        edit = True
        view = True
        archive = True
