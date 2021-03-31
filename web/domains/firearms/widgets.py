from django.forms.widgets import CheckboxSelectMultiple


class CheckboxSelectMultipleTable(CheckboxSelectMultiple):
    template_name = "forms/widgets/checkbox_select_table.html"
    option_template_name = "django/forms/widgets/input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Requires qs to be set on the form
        context["qs"] = self.qs
        context["process"] = self.process
        return context
