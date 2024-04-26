from web.forms.widgets import ICMSModelSelect2Widget


class EndorsementTemplateWidget(ICMSModelSelect2Widget):
    search_fields = [
        "template_name__icontains",
        "template_content__icontains",
    ]
