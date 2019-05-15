from django.contrib.auth import forms as auth_forms
from django import forms
from web import models
from captcha.fields import ReCaptchaField
from web.base.forms.widgets import (TextInput, PasswordInput)

import logging

logger = logging.getLogger(__name__)


class RegistrationForm(forms.ModelForm):

    confirm_email = forms.CharField(widget=forms.EmailInput(), max_length=254)
    confirm_security_answer = forms.CharField(max_length=254)

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    class Meta(forms.ModelForm):
        model = models.User
        fields = [
            'email', 'confirm_email', 'title', 'first_name', 'last_name',
            'phone', 'organisation', 'date_of_birth', 'security_question',
            'security_answer'
        ]
        labels = {
            'organisation': 'Organisation Name (Employer)',
            'email': 'Email',
            'first_name': 'Forename',
            'last_name': 'Surname',
            'phone': 'Telephone Number',
            'date_of_birth': 'Date of Birth'
        }


class CaptchaForm(forms.Form):
    captcha = ReCaptchaField()


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    new_password1 = forms.CharField(
        label='New password', strip=False, widget=PasswordInput())
    new_password2 = forms.CharField(
        label='Confirm New Password', strip=False, widget=PasswordInput())
    old_password = forms.CharField(strip=False, widget=PasswordInput())
    security_question = forms.CharField(disabled=True)
    security_answer = forms.CharField(max_length=4000, widget=PasswordInput())

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

        # Remove default Django help text list for new password
        self.fields['new_password1'].help_text = None

    def clean_security_answer(self):
        answer = self.cleaned_data['security_answer']
        if answer != self.user.security_answer:
            raise forms.ValidationError(
                ("Your security answer didn't match the one you gave us when\
                you created your account"))

        return answer


class AccessRequestForm(forms.ModelForm):
    class Meta(forms.ModelForm):
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
            'organisation_address': forms.Textarea({'rows': 5}),
            'description': forms.Textarea({'rows': 5}),
            'agent_address': forms.Textarea({'rows': 5})
        }


class UserDetailsUpdateForm(forms.ModelForm):
    address = forms.CharField(
        required=True,
        label='Work Address',
        widget=forms.Textarea({
            'rows': 5,
            'readonly': 'readonly'
        }))

    security_answer_repeat = forms.CharField(
        required=True,
        label="Re-enter Security Answer",
        widget=forms.PasswordInput(render_value=True))

    def __init__(self, *args, **kwargs):
        super(UserDetailsUpdateForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['share_contact_details'].required = True

    class Meta(forms.ModelForm):
        model = models.User

        fields = [
            'title', 'first_name', 'preferred_first_name', 'middle_initials',
            'last_name', 'organisation', 'department', 'job_title', 'address',
            'share_contact_details', 'date_of_birth', 'security_question',
            'security_answer'
        ]

        labels = {
            'first_name': 'Forename',
            'preferred_first_name': 'Preferred Forename',
            'last_name': 'Surname',
            'organisation': 'Organisation Name (Employer)',
            'department': 'Department Name (Employer)',
            'job_title': 'Job Title (Employer)',
            'share_contact_details': 'Share Contact Deails?'
        }

        widgets = {
            'share_contact_details':
            forms.Select(choices=((False, 'No'), (True, 'Yes'))),
            'security_question':
            forms.Textarea({'rows': 2}),
            'security_answer':
            forms.PasswordInput(render_value=True)
        }


class LoginForm(auth_forms.AuthenticationForm):
    username = auth_forms.UsernameField(
        widget=TextInput(attrs={'autofocus': True}))
    password = forms.CharField(strip=False, widget=PasswordInput)
