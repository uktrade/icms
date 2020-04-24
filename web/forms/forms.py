import datetime

from django.forms import ModelForm
from django_filters import FilterSet

from .mixins import (FiltersFieldConfigMixin, FormFieldConfigMixin,
                     ReadonlyFormMixin)


class ModelSearchFilter(FiltersFieldConfigMixin, FilterSet):
    pass


class ModelEditForm(FormFieldConfigMixin, ModelForm):
    pass


class ModelDisplayForm(ReadonlyFormMixin, ModelForm):
    pass


class ViewFlowForm(object):
    datetime_now = datetime.datetime.now().strftime(
        '%d-%b-%Y %H:%M:%S')  # use instead of ViewFlow management form
