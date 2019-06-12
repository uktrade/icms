from django.contrib.auth import forms as auth_forms
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from captcha.fields import ReCaptchaField
from web import models
from web.base.forms.widgets import (TextInput, Textarea, PasswordInput,
                                    EmailInput, Select)
from web.base.forms.fields import (CharField, PhoneNumberField, DateField)
from web.base.forms import (Form, ModelForm, FormConfigMetaClass)
from .utils import (validators, countries)

import logging

logger = logging.getLogger(__name__)


class RegistrationForm(ModelForm):

    # Pre-defined security question options
    FIRST_SCHOOL = "What is the name of your first school?"
    BEST_FRIEND = "What is the name of your childhood best friend?"
    MAIDEN_NAME = "What is your mother's maiden name?"
    OWN_QUESTION = "OWN_QUESTION"

    QUESTIONS = (('', 'Select One'), (FIRST_SCHOOL, FIRST_SCHOOL),
                 (BEST_FRIEND, BEST_FRIEND), (MAIDEN_NAME, MAIDEN_NAME),
                 (OWN_QUESTION, "I want to enter my own question"))

    telephone_number = PhoneNumberField()
    confirm_email = CharField(widget=EmailInput(), max_length=254)

    security_answer_repeat = CharField(
        required=True,
        label="Confirm Security Answer",
        widget=PasswordInput(render_value=True))

    security_question_list = CharField(
        label='Security Question', widget=Select(choices=QUESTIONS))

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_confirm_email(self):
        return validators.validate_email_confirmation(self)

    def clean_security_answer_repeat(self):
        return validators.validate_security_answer_confirmation(self)

    def clean_date_of_birth(self):
        return validators.validate_date_of_birth_not_in_future(self)

    class Meta:
        model = models.User
        fields = [
            'email', 'confirm_email', 'title', 'first_name', 'last_name',
            'telephone_number', 'organisation', 'date_of_birth',
            'security_question_list', 'security_question', 'security_answer'
        ]
        labels = {
            'organisation': _('Organisation Name (Employer)'),
            'email': _('Email'),
            'first_name': _('Forename'),
            'last_name': _('Surname'),
            'telephone_number': _('Telephone Number'),
            'date_of_birth': _('Date of Birth'),
            'security_question': _('Custom Question'),
            'security_answer': _('Security Answer')
        }

        widgets = {
            'security_answer': PasswordInput(render_value=True),
        }

        config = {
            'input': {
                'cols': 'six'
            },
            'label': {
                'cols': 'four'
            },
            'padding': {
                'right': 'two'
            },
            'actions': {
                'submit': {
                    'label': _('Register')
                },
                'link': {
                    'label': _('Cancel'),
                    'href': 'login'
                }
            },
        }


class CaptchaForm(Form):
    captcha = ReCaptchaField(label='Security Check')


class PasswordChangeForm(
        auth_forms.PasswordChangeForm, metaclass=FormConfigMetaClass):
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

    class Meta:
        config = {'actions': {'submit': {'label': _('Set password')}}}


class ResetPasswordForm(Form):
    login_id = CharField()
    captcha = ReCaptchaField()

    class Meta:
        config = {'actions': {'submit': {'label': 'Next'}}}


class ResetPasswordSecondForm(Form):
    question = CharField(widget=TextInput(attrs={'readonly': 'readonly'}))
    security_answer = CharField(label='Answer')
    date_of_birth = DateField()

    def __init__(self, user, *args, **kwargs):
        super(ResetPasswordSecondForm, self).__init__(*args, **kwargs)
        self.fields['question'].initial = user.security_question
        self.user = user

    def clean_security_answer(self):
        try:
            return validators.validate_security_answer(self)
        except ValidationError:
            self.add_error(None, 'Invalid details')

        return self.cleaned_data['security_answer']

    def clean_date_of_birth(self):
        try:
            return validators.validate_date_of_birth(self)
        except ValidationError:
            self.add_error(None, 'Invalid details')

    class Meta:
        config = {
            'actions': {
                'submit': {
                    'label': _('Reset password'),
                    'value': 'reset_password'
                }
            }
        }


class UserDetailsUpdateForm(ModelForm):

    # TODO: Save address to addresses table
    # address = CharField(
    #     required=True,
    #     label='Work Address',
    #     widget=Textarea({
    #         'rows': 5,
    #         'readonly': 'readonly'
    #     }))

    security_answer_repeat = CharField(
        required=True,
        label="Re-enter Security Answer",
        widget=PasswordInput(render_value=True))

    def __init__(self, *args, **kwargs):
        super(UserDetailsUpdateForm, self).__init__(*args, **kwargs)
        self.fields[
            'security_answer_repeat'].initial = self.instance.security_answer
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_security_answer_repeat(self):
        return validators.validate_security_answer_confirmation(self)

    class Meta:
        model = models.User

        fields = [
            'title', 'first_name', 'preferred_first_name', 'middle_initials',
            'last_name', 'organisation', 'department', 'job_title',
            'location_at_address', 'work_address', 'share_contact_details',
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
            'location_at_address': 'Floor/Room/Bay/Location',
            'work_address': 'Work Address'
        }

        widgets = {
            'share_contact_details':
            Select(choices=((False, 'No'), (True, 'Yes'))),
            'security_question': Textarea({'rows': 2}),
            'security_answer': PasswordInput(render_value=True),
            'location_at_address': Textarea({
                'rows': 2,
                'cols': 50
            }),
            'work_address': Textarea({
                'rows': 5,
                'readonly': 'readonly'
            })
        }

        help_texts = {
            'title':
            'Preferred form of address. Examples: Mr, Ms, Miss, Mrs, Dr, Rev, etc.',  # NOQA
            'first_name':
            'Formal given name',
            'preferred_first_name':
            'Preferred forename can be left blank. It is not used on formal document. Example Forename(Preferred): Robert (Bob)',  # NOQA
            'middle_initials':
            'Initials of middle names (if used)',
            'last_name':
            'Family or marriage name',
            'organisation':
            'Organisation name of direct employer. This is not the names of organisations which work may be carried out on behalf of, as this information is recorded elsewhere on the system.',  # NOQA
            'department':
            'Department name associated with, within direct employing organisation.',  # NOQA
            'job_title':
            'Job title used within direct employing organisation.',
            'location_at_address':
            _('Room or bay number and location within the formal postal address below.\nExample:\nROOM 104\nFIRST FLOOR REAR ANNEX'  # NOQA
              ),
            'work_address':
            _('Edit work address')
        }

        config = {
            'actions': {
                'padding': {
                    'left': None
                },
            }
        }


class LoginForm(auth_forms.AuthenticationForm, metaclass=FormConfigMetaClass):
    username = auth_forms.UsernameField(
        widget=TextInput(attrs={'autofocus': True}))
    password = CharField(strip=False, widget=PasswordInput)
    error_messages = {
        'invalid_login':
        _("Invalid username or password.<br/>N.B. passwords are case sensitive"
          ),
        'inactive':
        _("This account is inactive."),
    }

    class Meta:
        config = {
            'label': {
                'cols': 'three'
            },
            'input': {
                'cols': 'eight'
            },
            'padding': {
                'right': 'one'
            },
            'actions': {
                'submit': {
                    'label': 'Sign in'
                },
                'link': {
                    'href': 'reset-password',
                    'label': _('Forgot your password?')
                }
            },
        }


class PhoneNumberForm(ModelForm):
    telephone_number = CharField(validators=PhoneNumberField().validators)

    def __init__(self, *args, **kwargs):
        super(PhoneNumberForm, self).__init__(*args, **kwargs)
        self.fields['telephone_number'].initial = self.instance.phone

    def clean_telephone_number(self):
        phone = self.cleaned_data['telephone_number']
        self.instance.phone = phone
        return phone

    class Meta:
        model = models.PhoneNumber
        fields = ['telephone_number', 'type', 'comment']
        widgets = {'type': Select(choices=models.PhoneNumber.TYPES)}


class AlternativeEmailsForm(ModelForm):

    notifications = CharField(
        required=False, widget=Select(choices=((True, 'Yes'), (False, 'No'))))

    def __init__(self, *args, **kwargs):
        super(AlternativeEmailsForm, self).__init__(*args, **kwargs)
        self.fields['notifications'].initial = \
            self.instance.portal_notifications

    def clean_notifications(self):
        response = self.cleaned_data.get('notifications', None)
        self.instance.portal_notifications = True if response else False
        return response

    class Meta:
        model = models.AlternativeEmail
        fields = ['email', 'type', 'notifications', 'comment']

        widgets = {
            'email': EmailInput(),
            'type': Select(choices=models.Email.TYPES),
        }


class PersonalEmailForm(ModelForm):
    PRIMARY = 'PRIMARY'
    notifications = CharField(
        required=False,
        widget=Select(
            choices=((PRIMARY, 'Primary'), (True, 'Yes'), (False, 'No'))))

    def __init__(self, *args, **kwargs):
        super(PersonalEmailForm, self).__init__(*args, **kwargs)
        if self.instance.is_primary:
            self.fields['notifications'].initial = PersonalEmailForm.PRIMARY
        else:
            self.fields['notifications'].initial = \
                self.instance.portal_notifications

    def clean_notifications(self):
        response = self.cleaned_data.get('notifications', None)
        self.instance.is_primary = \
            True if response == PersonalEmailForm.PRIMARY else False
        self.instance.portal_notifications = True if response else False
        return response

    class Meta:
        model = models.PersonalEmail
        fields = ['email', 'type', 'notifications', 'comment']

        widgets = {
            'email': EmailInput(),
            'type': Select(choices=models.Email.TYPES),
        }


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
                'optional_indicators': False
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
    address = CharField(
        max_length=4000, widget=Textarea({
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
