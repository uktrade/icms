from copy import deepcopy

from django.forms import Form
# from django_filters import FilterSet

from web.utils import merge_dictionaries as m

default_field_config = {
    'label': {
        'cols': 'three',
        'prompt': 'west'
    },
    'input': {
        'cols': 'six'
    },
    'padding': {
        'right': 'three'
    },
    'show_optional_indicator': True
}

default_filter_config = m(default_field_config,
                          {'__all__': {
                              'show_optional_indicator': False
                          }})


class ProcessConfigMixin:
    """
    Adds form config to each form field.
    If it doesn't exit Uses default config
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meta = getattr(self, 'Meta', None)
        if meta:
            # Add config if not present
            config = getattr(meta, 'config', self._default_config)
            config = deepcopy(config)
            __all__ = config.pop('__all__', None)
            fields = self._get_fields()
            for key in fields.keys():
                conf = config.pop(key, None)
                field_config = m(self._default_config, __all__)
                field_config = m(field_config, conf)
                fields[key].config = field_config


class ReadonlyFormMixin(ProcessConfigMixin, Form):
    """ Makes forms read only, prevents changing any data"""
    _default_config = default_field_config

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            self.fields[key].disabled = True

    def _get_fields(self):
        return self.fields

    def save(self, *args, **kwargs):
        pass


class FormFieldConfigMixin(ProcessConfigMixin):
    """ Adds configuration for fields in the form from Form's inner Meta"""
    _default_config = default_field_config

    def _get_fields(self):
        return self.fields


class FiltersFieldConfigMixin(ProcessConfigMixin):
    """Adds configuration for fields from filterset's inner Meta"""
    _default_config = default_filter_config

    def _get_fields(self):
        return self.form.fields
