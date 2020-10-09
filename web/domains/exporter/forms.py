from django.forms import ModelForm
from django_filters import CharFilter, FilterSet

from .models import Exporter


class ExporterFilter(FilterSet):
    exporter_name = CharFilter(field_name="name", lookup_expr="icontains", label="Exporter Name")

    agent_name = CharFilter(field_name="agents__name", lookup_expr="icontains", label="Agent Name")

    class Meta:
        model = Exporter
        fields = []


class ExporterForm(ModelForm):
    class Meta:
        model = Exporter
        fields = ["name", "registered_number", "comments"]
        labels = {"name": "Organisation Name"}
