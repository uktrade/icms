from django.forms import widgets


class TextInput(widgets.TextInput):
    template_name = 'forms/widgets/input.html'


class PasswordInput(widgets.PasswordInput):
    template_name = 'forms/widgets/input.html'


class DateInput(widgets.DateInput):
    template_name = 'forms/widgets/date.html'
