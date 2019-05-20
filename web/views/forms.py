from django.contrib.auth import forms as auth_forms
from captcha.fields import ReCaptchaField
from web import models
from web.base.forms.widgets import (TextInput, Textarea, PasswordInput,
                                    EmailInput, Select)
from web.base.forms.fields import (CharField, PhoneNumberField)
from web.base.forms import (Form, ModelForm)
from .utils import validators

import logging

logger = logging.getLogger(__name__)


class RegistrationForm(ModelForm):

    telephone_number = PhoneNumberField()
    confirm_email = CharField(widget=EmailInput(), max_length=254)

    security_answer_repeat = CharField(
        required=True,
        label="Confirm Security Answer",
        widget=PasswordInput(render_value=True))

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_security_answer_repeat(self):
        return validators.validate_security_answer_confirmation(self)

    def clean_date_of_birth(self):
        return validators.validate_date_of_birth(self)

    class Meta:
        model = models.User
        fields = [
            'email', 'confirm_email', 'title', 'first_name', 'last_name',
            'telephone_number', 'organisation', 'date_of_birth',
            'security_question', 'security_answer'
        ]
        labels = {
            'organisation': 'Organisation Name (Employer)',
            'email': 'Email',
            'first_name': 'Forename',
            'last_name': 'Surname',
            'telephone_number': 'Telephone Number',
            'date_of_birth': 'Date of Birth'
        }

        widgets = {
            'security_answer': PasswordInput(render_value=True),
        }


class CaptchaForm(Form):
    captcha = ReCaptchaField()


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    new_password1 = CharField(
        label='New password', strip=False, widget=PasswordInput())
    new_password2 = CharField(
        label='Confirm New Password', strip=False, widget=PasswordInput())
    old_password = CharField(strip=False, widget=PasswordInput())
    security_question = CharField(disabled=True)
    security_answer = CharField(max_length=4000, widget=PasswordInput())

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

        # Remove default Django help text list for new password
        self.fields['new_password1'].help_text = None

    def clean_security_answer(self):
        return validators.validate_security_answer(self)


class AccessRequestForm(ModelForm):
    class Meta:
        model = models.AccessRequest

        fields = [
            'request_type', 'organisation_name', 'organisation_address',
            'description', 'agent_name', 'agent_address'
        ]

        labels = {
            'request_type':
            'Access Request Type',
            'description':
            'What are you importing and where are you importing it from?'
        }

        widgets = {
            'organisation_address': Textarea({'rows': 5}),
            'description': Textarea({'rows': 5}),
            'agent_address': Textarea({'rows': 5})
        }


class UserDetailsUpdateForm(ModelForm):
    address = CharField(
        required=True,
        label='Work Address',
        widget=Textarea({
            'rows': 5,
            'readonly': 'readonly'
        }))

    security_answer_repeat = CharField(
        required=True,
        label="Re-enter Security Answer",
        widget=PasswordInput(render_value=True))

    def __init__(self, *args, **kwargs):
        super(UserDetailsUpdateForm, self).__init__(*args, **kwargs)
        user = kwargs.get('instance')
        self.fields['security_answer_repeat'].initial = user.security_answer

    def clean_security_answer_repeat(self):
        return validators.validate_security_answer_confirmation(self)

    class Meta(ModelForm):
        model = models.User

        fields = [
            'title', 'first_name', 'preferred_first_name', 'middle_initials',
            'last_name', 'organisation', 'department', 'job_title',
            'location_at_address', 'address', 'share_contact_details',
            'date_of_birth', 'security_question', 'security_answer'
        ]

        labels = {
            'first_name': 'Forename',
            'preferred_first_name': 'Preferred Forename',
            'last_name': 'Surname',
            'organisation': 'Organisation Name (Employer)',
            'department': 'Department Name (Employer)',
            'job_title': 'Job Title (Employer)',
            'share_contact_details': 'Share Contact Deails?',
            'location_at_address': 'Floor/Room/Bay/Location'
        }

        widgets = {
            'share_contact_details':
            Select(choices=((False, 'No'), (True, 'Yes'))),
            'security_question': Textarea({'rows': 2}),
            'security_answer': PasswordInput(render_value=True),
            'location_at_address': Textarea({
                'rows': 2,
                'cols': 50
            })
        }

        help_texts = {
            'title':
            'Preferred form of address. Examples: Mr, Ms, Miss, Mrs, Dr, Rev, etc.',  # NOQA
            'first_name': 'Formal given name',
            'preferred_first_name':
            'Preferred forename can be left blank. It is not used on formal document. Example Forename(Preferred): Robert (Bob)',  # NOQA
            'middle_initials': 'Initials of middle names (if used)',
            'last_name': 'Family or marriage name',
            'organisation':
            'Organisation name of direct employer. This is not the names of organisations which work may be carried out on behalf of, as this information is recorded elsewhere on the system.',  # NOQA
            'department':
            'Department name associated with, within direct employing organisation.',  # NOQA
            'job_title':
            'Job title used within direct employing organisation.',
            'location_at_address':
            'Room or bay number and location within the formal postal address below.\nExample:\nROOM 104\nFIRST FLOOR REAR ANNEX',  # NOQA
            'address': 'Edit work address',  # NOQA
        }


class LoginForm(auth_forms.AuthenticationForm):
    username = auth_forms.UsernameField(
        widget=TextInput(attrs={'autofocus': True}))
    password = CharField(strip=False, widget=PasswordInput)


class PhoneNumberForm(ModelForm):
    telephone_number = PhoneNumberField()

    def __init__(self, *args, **kwargs):
        super(PhoneNumberForm, self).__init__(*args, **kwargs)
        self.fields['telephone_number'].initial = self.instance.phone

    def clean_telephone_number(self):
        phone = self.cleaned_data['telephone_number']
        self.instance.phone = phone
        return phone

    class Meta:
        model = models.PhoneNumber
        fields = ['type', 'comment']

        widgets = {'type': Select(choices=models.PhoneNumber.TYPES)}
