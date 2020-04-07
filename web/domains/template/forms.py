from django import forms
from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelSearchFilter, ModelEditForm

from .models import Template


class GenericTemplate(ModelEditForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_labels(self.instance.template_type)
        self.enable_html_editor()

    def set_labels(self, template_type):
        if template_type == Template.EMAIL_TEMPLATE:
            self.fields['template_title'].label = "Email Subject"
            self.fields['template_content'].label = "Email Body"

    def enable_html_editor(self, template_type):
        """
            Sets lang=html on textarea boxes that need to show an html editor
        """
        if template_type in (Template.EMAIL_TEMPLATE,):
            self.fields['template_content'].widget = forms.Textarea(
                attrs={'lang': 'html'}
            )

    class Meta:
        model = Template
        fields = ['template_name', 'template_title', 'template_content']


class TemplatesFilter(ModelSearchFilter):
    # Fields of the model that can be filtered
    template_name = CharFilter(lookup_expr='icontains',
                               label='Template Name')
    application_domain = ChoiceFilter(choices=Template.DOMAINS,
                                      lookup_expr='exact',
                                      label='Application Domain')
    template_type = ChoiceFilter(choices=Template.TYPES,
                                 lookup_expr='exact',
                                 label='Template Type')
    template_title = CharFilter(lookup_expr='icontains',
                                label='Template Title')
    template_content = CharFilter(lookup_expr='icontains',
                                  label='Template Content')
    is_active = ChoiceFilter(choices=Template.STATUS,
                             lookup_expr='exact',
                             label='Template Status')

    class Meta:
        model = Template
        fields = []  # Django complains without fields set in the meta
