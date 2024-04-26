from web.forms.widgets import ICMSModelSelect2Widget


class ImporterWidget(ICMSModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "registered_number__icontains",
        "eori_number__icontains",
        "user__first_name__icontains",
        "user__email__icontains",
    ]

    def label_from_instance(self, importer):
        return importer.display_name


class ImporterAgentWidget(ImporterWidget):
    """Used when linking an agent for an access request."""

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"link": "main_importer"}
