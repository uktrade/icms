from django.forms import Form
from django.forms.fields import CharField
from django.forms.widgets import Select, Textarea, TextInput
from django.utils.translation import gettext_lazy as _
from web.forms import validators
from web.views.utils import countries


class PostCodeSearchForm(Form):
    post_code = CharField(required=True, label=_('Postcode'))
    country = CharField(
        required=False,
        widget=Select(choices=countries.get()),
        help_text="Choose a country to begin manually entering the address")

    class Meta:
        config = {
            'label': {
                'cols': 'three',
                'optional_indicators': False,
                'prompt': 'north'
            },
            'input': {
                'cols': 'eight'
            },
            'actions': {
                'submit': {
                    'label': 'Search',
                    'name': 'action',
                    'value': 'search_address'
                }
            },
        }


class ManualAddressEntryForm(Form):
    country = CharField(widget=TextInput({'readonly': 'readonly'}))
    address = CharField(max_length=4000,
                        widget=Textarea({
                            'rows': 6,
                            'cols': 50
                        }))

    def clean_address(self):
        return validators.validate_manual_address(self)

    class Meta:
        config = {
            'actions': {
                'submit': {
                    'label': _('Save Address'),
                    'name': 'action',
                    'value': 'save_manual_address'
                },
                'link': {
                    'label': _('Cancel'),
                    'attrs': {
                        'onclick': 'window.history.back(); return false;'
                    }
                }
            }
        }
