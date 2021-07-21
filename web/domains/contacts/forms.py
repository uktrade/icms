from django import forms

from web.models import User

from .widgets import ContactWidget


class ContactForm(forms.Form):
    contact = forms.ModelChoiceField(
        label="",
        help_text=(
            "Search a contact to add. Contacts returned are matched against first/last name,"
            " email, job title, organisation and department."
        ),
        queryset=User.objects.filter(is_active=True),
        widget=ContactWidget(
            attrs={
                "data-minimum-input-length": 0,
                "data-placeholder": "-- Search user",
            }
        ),
    )

    def __init__(self, *args, contacts_to_exclude=None, **kwargs):
        super().__init__(*args, **kwargs)

        if contacts_to_exclude:
            contacts = self.fields["contact"].queryset
            self.fields["contact"].queryset = contacts.exclude(pk__in=contacts_to_exclude)
