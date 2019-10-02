from django.urls import reverse_lazy
from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)

from .forms import (ProductLegislationDisplayForm, ProductLegislationFilter,
                    ProductLegislationForm)
from .models import ProductLegislation


class ProductLegislationListView(ModelFilterView):
    template_name = 'web/product-legislation/list.html'
    filterset_class = ProductLegislationFilter
    model = ProductLegislation
    config = {'title': 'Maintain Product Legislation'}

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
    config = {'title': 'Create Product Legislation'}


class ProductLegislationUpdateView(ModelUpdateView):
    template_name = 'web/product-legislation/edit.html'
    form_class = ProductLegislationForm
    model = ProductLegislation
    success_url = reverse_lazy('product-legislation-list')
    config = {'title': 'Edit Product Legislation'}


class ProductLegislationDetailView(ModelDetailView):
    template_name = 'web/product-legislation/edit.html'
    model = ProductLegislation
    config = {'title': 'View Product Legislation'}

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ProductLegislationDisplayForm(instance=object)
        return context
