from captcha.fields import ReCaptchaField
from django.contrib.auth.forms import (AuthenticationForm, PasswordChangeForm,
                                       UsernameField)
from django.forms import Form, ModelForm, ValidationError
from django.forms.fields import CharField, DateField
from django.forms.widgets import PasswordInput, Select, TextInput
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django import forms
from web.domains.user import User
from web.forms import validators
from web.forms.fields import PhoneNumberField
from web.forms.mixins import FormFieldConfigMixin
from web.forms.widgets import DateInput


class LoginForm(FormFieldConfigMixin, AuthenticationForm):
    username = UsernameField(widget=TextInput(attrs={'autofocus': True}))
    password = CharField(strip=False, widget=PasswordInput)
    error_status = None

    def confirm_login_allowed(self, user):
        if user.account_status in [User.BLOCKED, User.SUSPENDED, User.CANCELLED]:
            self.error_status = user.account_status.lower()
            raise forms.ValidationError(f'User {self.error_status}.')
        elif user.password_disposition != 'FULL':
            return redirect('set-password')

    class Meta:
        config = {
            '__all__': {
                'label': {
                    'cols': 'three',
                },
                'input': {
                    'cols': 'nine'
                },
                'padding': {
                    'right': None
                },
                'show_optional_indicator': False
            }
        }


class RegistrationForm(FormFieldConfigMixin, ModelForm):
    # Pre-defined security question options
    FIRST_SCHOOL = "What is the name of your first school?"
    BEST_FRIEND = "What is the name of your childhood best friend?"
    MAIDEN_NAME = "What is your mother's maiden name?"
    OWN_QUESTION = "OWN_QUESTION"

    QUESTIONS = (('', 'Select One'), (FIRST_SCHOOL, FIRST_SCHOOL),
                 (BEST_FRIEND, BEST_FRIEND), (MAIDEN_NAME, MAIDEN_NAME),
                 (OWN_QUESTION, "I want to enter my own question"))

    telephone_number = PhoneNumberField()
    confirm_email = CharField(max_length=254)

    security_answer_repeat = CharField(required=True,
                                       label="Confirm Security Answer",
                                       widget=PasswordInput(render_value=True))
    security_question_list = CharField(label='Security Question',
                                       widget=Select(choices=QUESTIONS))

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
        model = User
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
            'date_of_birth': DateInput()
        }

        config = {
            '__all__': {
                'label': {
                    'cols': 'four'
                },
                'input': {
                    'cols': 'six'
                },
                'padding': {
                    'right': 'two'
                }
            }
        }


class CaptchaForm(FormFieldConfigMixin, Form):
    captcha = ReCaptchaField(label='Security Check')

    class Meta:
        config = RegistrationForm.Meta.config


class ResetPasswordForm(FormFieldConfigMixin, Form):
    login_id = CharField()
    captcha = ReCaptchaField()

    class Meta:
        config = {
            '__all__': {
                'label': {
                    'cols': 'four',
                },
                'input': {
                    'cols': 'four'
                },
                'padding': {
                    'right': 'four'
                },
                'show_optional_indicator': False
            }
        }


class ResetPasswordSecondForm(FormFieldConfigMixin, Form):
    question = CharField(widget=TextInput(attrs={'readonly': 'readonly'}))
    security_answer = CharField(label='Answer')
    date_of_birth = DateField(widget=DateInput())

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
        config = ResetPasswordForm.Meta.config


class PasswordChangeForm(FormFieldConfigMixin, PasswordChangeForm):
    new_password1 = CharField(label='New password',
                              strip=False,
                              widget=PasswordInput())
    new_password2 = CharField(label='Confirm New Password',
                              strip=False,
                              widget=PasswordInput())
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
        config = ResetPasswordForm.Meta.config
