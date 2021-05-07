from django import forms

from . import models


class PrepareDFLForm(forms.ModelForm):
    class Meta:
        model = models.DFLApplication
        fields = ("know_bought_from",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True

        # The default label for unknown is "Unknown"
        self.fields["know_bought_from"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]
