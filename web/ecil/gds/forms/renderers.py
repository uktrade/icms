from django.forms.renderers import TemplatesSetting


class GDSTemplateSetting(TemplatesSetting):
    # Custom form renderer to display the error summary
    form_template_name = "gds/forms/div.html"
    # Custom field renderer to handle rendering govuk-frontend-jinja macros
    field_template_name = "gds/forms/field.html"
