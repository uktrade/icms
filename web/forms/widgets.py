import django.forms.widgets as widgets
from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget


class DateInput(widgets.DateInput):
    template_name = "forms/widgets/date.html"


class RadioSelect(widgets.RadioSelect):
    option_template_name = "forms/widgets/radio_option.html"
    display_inline = False

    def __init__(self, attrs=None, choices=()):
        if attrs is None:
            attrs = {}

        # Used to style the `ul` and input
        attrs["class"] = self.display_inline and "radio-input-inline" or "radio-input"

        super().__init__(attrs, choices)


class RadioSelectInline(RadioSelect):
    display_inline = True


# Used for boolean fields
YesNoRadioSelectInline = RadioSelectInline(choices=((True, "Yes"), (False, "No")))

#  class Textarea(Textarea):
#      template_name = 'forms/widgets/textarea.html'

#  class EmailInput(EmailInput):
#      template_name = 'forms/widgets/input.html'

#  class Select(Select):
#      template_name = 'forms/widgets/select.html'

#  class Display(TextInput):
#      """ Widget to display the field as text"""
#    template_name = 'forms/widgets/input.html'

#  class Hiddennput(HiddenInput):
#      pass

#  class CheckboxInput(CheckboxInput):
#      pass


class CheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    option_template_name = "forms/widgets/checkbox_option.html"

    def __init__(self, attrs=None, choices=()):
        if attrs is None:
            attrs = {}

        # Used to style the `ul` and input
        attrs["class"] = "radio-input"

        super().__init__(attrs, choices)


class JoditTextArea(widgets.Textarea):
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}

        # Setting this class means web/js/components/text-editor.js can initialise
        # this textarea as a jodit editor.
        attrs["class"] = "icms-jodit-editor"

        super().__init__(attrs)


class LoginRequiredSelect2WidgetMixin:
    def __init__(self, *args, **kwargs):
        kwargs["data_view"] = "login-required-select2-view"
        super().__init__(*args, **kwargs)


class ICMSModelSelect2Widget(LoginRequiredSelect2WidgetMixin, ModelSelect2Widget):
    """ModelSelect2Widget requiring a user to be logged in to IMCS."""

    ...


class ICMSModelSelect2MultipleWidget(ModelSelect2MultipleWidget):
    """ModelSelect2MultipleWidget requiring a user to be logged in to IMCS."""

    ...
