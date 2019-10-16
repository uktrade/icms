from django.urls import reverse_lazy
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import ProductLegislationFilter, ProductLegislationForm
from .models import ProductLegislation

permissions = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'


class ProductLegislationListView(ModelFilterView):
    template_name = 'web/product-legislation/list.html'
    filterset_class = ProductLegislationFilter
    model = ProductLegislation
    page_title = 'Maintain Product Legislation'
    permission_required = permissions

    class Display:
        fields = [
            'name', 'is_biocidal_yes_no', 'is_biocidal_claim_yes_no',
            'is_eu_cosmetics_regulation_yes_no'
        ]
        headers = [
            'Legislation Name', 'Is Biocidal', 'Is Biocidal Claim',
            'Is EU Cosmetics Regulation'
        ]
        view = True
        archive = True
        edit = True


class ProductLegislationCreateView(ModelCreateView):
    template_name = 'web/product-legislation/edit.html'
    form_class = ProductLegislationForm
    model = ProductLegislation
    success_url = reverse_lazy('product-legislation-list')
    cancel_url = success_url
    page_title = 'New Product Legislation'
    permission_required = permissions


class ProductLegislationUpdateView(ModelUpdateView):
    template_name = 'web/product-legislation/edit.html'
    form_class = ProductLegislationForm
    model = ProductLegislation
    success_url = reverse_lazy('product-legislation-list')
    cancel_url = success_url
    permission_required = permissions


class ProductLegislationDetailView(ModelDetailView):
    template_name = 'web/product-legislation/view.html'
    model = ProductLegislation
    form_class = ProductLegislationForm
    cancel_url = reverse_lazy('product-legislation-list')
    permission_required = permissions
