from django import forms
from guardian.shortcuts import get_users_with_perms

from web.models import User

from . import models


class PrepareDFLForm(forms.ModelForm):

    contact = forms.ModelChoiceField(
        queryset=User.objects.none(),
        help_text=(
            "Select the main point of contact for the case. "
            "This will usually be the person who created the application."
        ),
    )

    class Meta:
        model = models.DFLApplication
        fields = ("contact", "know_bought_from")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["know_bought_from"].required = True

        # The default label for unknown is "Unknown"
        self.fields["know_bought_from"].widget.choices = [
            ("unknown", "---------"),
            ("true", "Yes"),
            ("false", "No"),
        ]

        users = get_users_with_perms(
            self.instance.importer, only_with_perms_in=["is_contact_of_importer"]
        )
        self.fields["contact"].queryset = users.filter(is_active=True)
