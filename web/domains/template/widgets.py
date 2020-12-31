from django_select2 import forms as s2forms


class EndorsementTemplateWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "template_name__icontains",
        "template_content__icontains",
    ]
