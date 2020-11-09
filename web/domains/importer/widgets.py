from django_select2 import forms as s2forms


class ImporterWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "registered_number__icontains",
        "eori_number__icontains",
        "eori_number_ni__icontains",
        "user__first_name__icontains",
        "user__email__icontains",
    ]

    def label_from_instance(self, importer):
        return importer.display_name
