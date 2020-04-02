from django.urls import reverse_lazy

from web.views import ModelFilterView, ModelDetailView
from web.views.actions import Archive, Unarchive, Edit

from .models import Template
from .forms import TemplatesFilter, GenericTemplate


class TemplateListView(ModelFilterView):
    template_name = 'web/template/list.html'
    model = Template
    filterset_class = TemplatesFilter
    page_title = 'Maintain Templates'
    permission_required = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

    # Default display fields on the listing page of the model
    class Display:
        fields = [
            'template_name', 'application_domain_verbose',
            'template_type_verbose', 'template_status'
        ]
        fields_config = {
            'template_name': {
                'header': 'Template Name',
                'link': True
            },
            'application_domain_verbose': {
                'header': 'Application Domain'
            },
            'template_type_verbose': {
                'header': 'Template Type'
            },
            'template_status': {
                'header': 'Template Status'
            }
        }
        actions = [Archive(), Unarchive(), Edit()]


class TemplateDetailView(ModelDetailView):
    form_class = GenericTemplate
    model = Template
    permission_required = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'
    success_url = "javascript:history.go(-1)"
    cancel_url = success_url
