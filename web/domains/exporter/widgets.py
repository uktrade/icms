from web.forms.widgets import ICMSModelSelect2Widget


class ExporterWidget(ICMSModelSelect2Widget):
    search_fields = [
        "name__icontains",
        "registered_number__icontains",
    ]

    def label_from_instance(self, exporter):
        return exporter.name


class ExporterAgentWidget(ExporterWidget):
    """Used when linking an agent for an access request."""

    # Key is a name of a field in a form.
    # Value is a name of a field in a model (used in `queryset`).
    dependent_fields = {"link": "main_exporter"}
