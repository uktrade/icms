import datetime

from django.forms import ModelForm
from django_filters import FilterSet

from .mixins import (FiltersFieldConfigMixin, FormFieldConfigMixin,
                     ReadonlyFormMixin)


class ModelSearchFilter(FiltersFieldConfigMixin, FilterSet):
    pass


class ModelEditForm(FormFieldConfigMixin, ModelForm):
    pass


class ViewFlowModelEditForm(ModelEditForm):
    datetime_now = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')  # use instead of ViewFlow management form


class ModelDisplayForm(ReadonlyFormMixin, ModelForm):
    pass
