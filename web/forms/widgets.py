import django.forms.widgets as widgets


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
