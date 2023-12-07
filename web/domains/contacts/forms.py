from django import forms

from web.forms.widgets import YesNoRadioSelectInline
from web.models import User

from .widgets import ContactWidget


class ContactForm(forms.Form):
    contact = forms.ModelChoiceField(
        label="",
        help_text=(
            "Search a contact to add. Contacts returned are matched against first/last name,"  # /PS-IGNORE
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


class InviteOrgContactForm(forms.Form):
    first_name = forms.CharField(help_text="Your contact's first name")  # /PS-IGNORE
    last_name = forms.CharField(help_text="Your contact's last name")  # /PS-IGNORE
    email = forms.EmailField(help_text="Email address used to log in to GOV.UK One Login")


class AcceptOrgInviteForm(forms.Form):
    accept_invite = forms.BooleanField(
        label="Would you like to accept this invite?",
        required=False,
        widget=YesNoRadioSelectInline,
        initial=False,
    )
