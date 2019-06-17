from django.forms.widgets import (TextInput, Textarea, PasswordInput,
                                  DateInput, EmailInput, Select, HiddenInput,
                                  CheckboxInput)


class TextInput(TextInput):
    template_name = 'forms/widgets/input.html'


class PasswordInput(PasswordInput):
    template_name = 'forms/widgets/input.html'


class DateInput(DateInput):
    template_name = 'forms/widgets/date.html'


class Textarea(Textarea):
    template_name = 'forms/widgets/textarea.html'


class EmailInput(EmailInput):
    template_name = 'forms/widgets/input.html'


class Select(Select):
    template_name = 'forms/widgets/select.html'


class Display(TextInput):
    """ Widget to display the field as text"""
    template_name = 'forms/widgets/input.html'


class CheckboxInput(CheckboxInput):
    pass
