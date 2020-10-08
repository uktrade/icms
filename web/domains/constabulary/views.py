from django.urls import reverse_lazy

from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, Edit, Unarchive

from .forms import ConstabulariesFilter, ConstabularyForm
from .models import Constabulary


class ConstabularyListView(ModelFilterView):
    template_name = "web/domains/constabulary/list.html"
    model = Constabulary
    filterset_class = ConstabulariesFilter
    permission_required = "web.reference_data_access"
    page_title = "Maintain Constabularies"

    class Display:
        fields = ["name", "region_verbose", "email"]
        fields_config = {
            "name": {"header": "Constabulary Name", "link": True},
            "region_verbose": {"header": "Constabulary Region"},
            "email": {"header": "Email Address"},
        }
        actions = [Archive(), Unarchive(), Edit()]


class ConstabularyCreateView(ModelCreateView):
    template_name = "web/domains/constabulary/edit.html"
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy("constabulary-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"
    page_title = "New Constabulary"


class ConstabularyEditView(ModelUpdateView):
    template_name = "web/domains/constabulary/edit.html"
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy("constabulary-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"


class ConstabularyDetailView(ModelDetailView):
    form_class = ConstabularyForm
    model = Constabulary
    success_url = reverse_lazy("constabulary-list")
    cancel_url = success_url
    permission_required = "web.reference_data_access"
