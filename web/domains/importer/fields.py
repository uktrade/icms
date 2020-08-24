from django_select2 import forms as s2forms


class PersonWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
        "email__icontains",
        "title__icontains",
    ]
