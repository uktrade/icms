from django.db.models import QuerySet
from django.urls import reverse_lazy

from web.permissions import Perms
from web.views import ModelCreateView, ModelDetailView, ModelFilterView, ModelUpdateView
from web.views.actions import Archive, Edit, Unarchive

from .forms import ProductLegislationFilter, ProductLegislationForm
from .models import ProductLegislation


class ProductLegislationListView(ModelFilterView):
    template_name = "web/domains/legislation/list.html"
    filterset_class = ProductLegislationFilter
    model = ProductLegislation
    page_title = "Maintain Product Legislation"
    permission_required = Perms.sys.ilb_admin
    paginate = False

    def get_initial_data(self, queryset: QuerySet) -> QuerySet:
        return queryset

    class Display:
        fields = [
            "name",
            "is_biocidal_yes_no",
            "is_biocidal_claim_yes_no",
            "is_eu_cosmetics_regulation_yes_no",
            "is_gb_legislation",
            "is_ni_legislation",
        ]

        fields_config = {
            "name": {"header": "Legislation Name", "link": True},
            "is_biocidal_yes_no": {"header": "Is Biocidal"},
            "is_biocidal_claim_yes_no": {"header": "Is Biocidal Claim"},
            "is_eu_cosmetics_regulation_yes_no": {"header": "Is Cosmetics Regulation"},
            "is_gb_legislation": {"header": "Great Britain Legislation"},
            "is_ni_legislation": {"header": "Northern Ireland Legislation"},
        }

        actions = [Archive(), Unarchive(), Edit(hide_if_archived_object=True)]


class ProductLegislationCreateView(ModelCreateView):
    template_name = "web/domains/legislation/edit.html"
    form_class = ProductLegislationForm
    model = ProductLegislation
    success_url = reverse_lazy("product-legislation-list")
    cancel_url = success_url
    page_title = "New Product Legislation"
    permission_required = Perms.sys.ilb_admin


class ProductLegislationUpdateView(ModelUpdateView):
    template_name = "web/domains/legislation/edit.html"
    form_class = ProductLegislationForm
    model = ProductLegislation
    success_url = reverse_lazy("product-legislation-list")
    cancel_url = success_url
    permission_required = Perms.sys.ilb_admin


class ProductLegislationDetailView(ModelDetailView):
    template_name = "web/domains/legislation/view.html"
    model = ProductLegislation
    form_class = ProductLegislationForm
    cancel_url = reverse_lazy("product-legislation-list")
    permission_required = Perms.sys.ilb_admin
