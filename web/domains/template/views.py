from django.urls import reverse_lazy

from web.views import ModelFilterView, ModelDetailView, ModelUpdateView, ModelCreateView
from web.views.actions import Archive, Unarchive, Edit

from .models import Template
from .forms import TemplatesFilter, GenericTemplate, EndorsementCreateTemplateForm

permissions = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'


class TemplateListView(ModelFilterView):
    template_name = 'web/domains/template/list.html'
    model = Template
    filterset_class = TemplatesFilter
    page_title = 'Maintain Templates'
    permission_required = permissions

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
    permission_required = permissions
    cancel_url = "javascript:history.go(-1)"


class TemplateEditView(ModelUpdateView):
    template_name = 'web/domains/template/edit.html'
    form_class = GenericTemplate
    model = Template
    success_url = reverse_lazy('template-list')
    cancel_url = success_url
    permission_required = permissions


class EndorsementCreateView(ModelCreateView):
    template_name = 'web/domains/template/edit.html'
    form_class = EndorsementCreateTemplateForm
    model = Template
    success_url = reverse_lazy('template-list')
    cancel_url = success_url
    permission_required = permissions
    page_title = 'New Endorsement'

    def form_valid(self, form):
        """
            Sets readonly fields for this template type and validates other inputs.
        """
        template = form.instance

        template.template_type = Template.ENDORSEMENT
        template.application_domain = Template.IMPORT_APPLICATION

        return super().form_valid(form)
