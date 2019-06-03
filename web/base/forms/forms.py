# import json
# from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import (CharField, DateField)
from django import forms
from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.models import ModelFormMetaclass
from django_filters.filterset import FilterSetMetaclass
from web.base.utils import dict_merge
from . import widgets
import django_filters as filter


class DefaultFormConfig(object):
    """ Form config metaclass adds config in form's inner Meta to context of
    the view
    """

    #  Default configuration is merged with form's configuration in
    #  its inner 'Meta'. Form's config takes precedence.
    _config = {
        'label': {
            'cols': 'four',
            'optional_indicators': True
        },
        'input': {
            'cols': 'four'
        },
        'padding': {
            'right': 'four',
            'left': ''
        },
        'actions': {
            'padding': {
                'left': 'four',
                'right': None
            },
            'cols': '',  # Same as input.cols if not given
            'submit': {
                'name': 'action',
                'value': 'save',
                'label': 'Save'
            },
            'link': {
                'href': '',
                'label': '',
                'attrs': {}
            },
        },
        'errors': {
            'non_field': True
        }
    }

    # Adapted from:
    # https://www.xormedia.com/recursively-merge-dictionaries-in-python/
    @staticmethod
    def new_form_meta(cls, attrs):
        meta = attrs.get('Meta', None)
        """Convert declarative form configuration to class attribute"""
        if meta and hasattr(meta, 'config'):
            # Merge user defined config with default config
            cls.config = dict_merge(DefaultFormConfig._config, meta.config)
        else:
            cls.config = DefaultFormConfig._config
        return cls


class FormConfigMetaClass(DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super(FormConfigMetaClass, mcs).__new__(
            mcs, name, bases, attrs)
        return DefaultFormConfig.new_form_meta(new_class, attrs)


class ModelFormConfigMetaClass(ModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelFormConfigMetaClass, mcs).__new__(
            mcs, name, bases, attrs)
        return DefaultFormConfig.new_form_meta(new_class, attrs)


class FilterFormConfigMetaClass(FilterSetMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super(FilterFormConfigMetaClass, mcs).__new__(
            mcs, name, bases, attrs)
        return DefaultFormConfig.new_form_meta(new_class, attrs)


def get_field(field, **kwargs):
    widget = kwargs.pop('widget', None)
    if not widget:
        if isinstance(field, CharField):
            widget = widgets.TextInput()
        elif isinstance(field, DateField):
            widget = widgets.DateInput

    return field.formfield(widget=widget, **kwargs)


class ModelForm(forms.ModelForm, metaclass=ModelFormConfigMetaClass):
    """Model form to customise widgets and their templates"""

    class Meta:
        formfield_callback = get_field


class Form(forms.Form, metaclass=FormConfigMetaClass):
    pass


class FilterSet(filter.FilterSet, metaclass=FilterFormConfigMetaClass):
    pass


# class FormSerializeMixin(object):
#     def data_dict(self):
#         data = {}
#         fields = self.Meta.serialize if hasattr(
#             self.Meta, 'serialize') else self.Meta.fields
#         for field in fields:
#             value = self.cleaned_data.get(field, None)
#             if value:
#                 data[field] = self.cleaned_data.get(field, None)
#         return data

#     def serialize(self):
#         return json.dumps(self.data_dict(), cls=DjangoJSONEncoder)
