from django import forms

from web.forms.widgets import YesNoRadioSelectInline


class CookieConsentForm(forms.Form):
    accept_cookies = forms.BooleanField(
        label="Do you want to accept analytics cookies?",
        required=False,
        widget=YesNoRadioSelectInline,
    )
