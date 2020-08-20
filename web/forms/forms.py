from django.forms import ModelForm
from django_filters import FilterSet

from .mixins import ReadonlyFormMixin


class ModelSearchFilter(FilterSet):
    pass


class ModelEditForm(ModelForm):
    pass


class ModelDisplayForm(ReadonlyFormMixin, ModelForm):
    pass
