from django_select2 import forms as s2forms


class ExporterWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "registered_number__icontains",
    ]

    def label_from_instance(self, exporter):
        return exporter.name
