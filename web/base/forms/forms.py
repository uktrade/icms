from django.db.models import (CharField, DateField)
from django.forms import (Form, ModelForm)
from . import widgets


def get_field(field, **kwargs):
    widget = kwargs.pop('widget', None)
    if not widget:
        if isinstance(field, CharField):
            widget = widgets.TextInput()
        elif isinstance(field, DateField):
            widget = widgets.DateInput

    return field.formfield(widget=widget, **kwargs)


class ModelForm(ModelForm):
    """Model form to customise widgets and their templates"""

    class Meta:
        formfield_callback = get_field


class Form(Form):
    pass
