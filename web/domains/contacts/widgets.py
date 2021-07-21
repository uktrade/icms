from django_select2 import forms as s2forms


class ContactWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
        "email__icontains",
        "job_title__icontains",
        "organisation__icontains",
        "department__icontains",
    ]

    def label_from_instance(self, user):
        return f"{user.full_name} - {user.email}"
