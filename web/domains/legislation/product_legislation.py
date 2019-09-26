from django.urls import reverse_lazy
from web.base.forms import FilterSet, ModelForm, widgets, ReadOnlyFormMixin
from web.base.views import (SecureUpdateView, SecureCreateView,
                            SecureFilteredListView, SecureDetailView)
from web.models import ProductLegislation
from web.base.utils import dict_merge
from django_filters import (CharFilter, ChoiceFilter)
