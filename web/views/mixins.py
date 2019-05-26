from django.forms import CharField, BaseForm
from django.forms.widgets import HiddenInput


class MainFormMixin(BaseForm):
    scroll_position = CharField(widget=HiddenInput)
