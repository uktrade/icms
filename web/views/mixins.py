from django.forms import IntegerField
from django.forms.widgets import HiddenInput


class MainFormMixin(object):
    scroll_position = IntegerField(widget=HiddenInput)
