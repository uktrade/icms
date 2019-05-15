from django.db import models
from django import forms
from . import widgets


def get_field(f):
    if isinstance(f, models.CharField):
        return forms.TextInput(widget=widgets.TextInput)
    else:
        return f.formfield()


class ModelForm(forms.ModelForm):
    class Meta:
        formfield_callback = get_field
