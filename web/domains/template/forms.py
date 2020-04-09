from django import forms
from django_filters import CharFilter, ChoiceFilter
from web.forms import ModelSearchFilter, ModelEditForm

from .models import Template


class GenericTemplate(ModelEditForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_fields(self.instance.template_type)
        self.enable_html_editor(self.instance.template_type)

    def set_fields(self, template_type):
        if template_type == Template.EMAIL_TEMPLATE:
            self.fields['template_title'].label = "Email Subject"
            self.fields['template_content'].label = "Email Body"

        if template_type == Template.LETTER_TEMPLATE:
            del (self.fields['template_title'])
            self.fields['template_content'].label = "Letter"

        if template_type == Template.DECLARATION:
            self.fields['template_title'].label = "Declaration Title"
            self.fields['template_content'].label = "Declaration Text"
            self.fields['template_content'].help_text = "This will be displayed as the main text of the Submit page"

        if template_type == Template.ENDORSEMENT:
            self.fields['template_title'].label = "Endorsment Title"
            self.fields['template_content'].label = "Endorsement Text"

        if template_type == Template.LETTER_FRAGMENT:
            del (self.fields['template_title'])
            self.fields['template_name'].label = "Fragment Name"
            self.fields['template_content'].label = "Fragment Text"

    def enable_html_editor(self, template_type):
        """
            Sets lang=html on textarea boxes that need to show an html editor
        """
        if template_type in (Template.LETTER_TEMPLATE, Template.LETTER_FRAGMENT,):
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
