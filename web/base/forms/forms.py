from django.db import models
from django import forms
from . import widgets


def get_template_name(widget):
    if isinstance(widget, forms.CharField):
        return widgets.TextInput.template_name
    elif isinstance(widget, forms.DateField):
        return widgets.DateInput.template_name
    elif isinstance(widget, forms.PasswordInput):
        return widgets.PasswordInput.template_name
    else:
        return widget.template_name


def get_field(field, **kwargs):
    widget = kwargs.pop('widget', None)
    if not widget:
        if isinstance(field, models.CharField):
            widget = widgets.TextInput()
        elif isinstance(field, models.DateField):
            widget = widgets.DateInput

    return field.formfield(widget=widget, **kwargs)


class ModelForm(forms.ModelForm):
    """Model form to customise widgets and their templates"""

    class Meta:
        formfield_callback = get_field
