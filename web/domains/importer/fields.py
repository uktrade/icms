from web.forms.widgets import ICMSModelSelect2Widget


class PersonWidget(ICMSModelSelect2Widget):
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
        "email__icontains",
        "title__icontains",
    ]
