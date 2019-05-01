from django.contrib.auth import forms as auth_forms
from django import forms
from . import models
from captcha.fields import ReCaptchaField

import logging

logger = logging.getLogger(__name__)


class RegistrationForm(forms.ModelForm):

    confirm_email = forms.CharField(widget=forms.EmailInput(), max_length=254)
    confirm_security_answer = forms.CharField(max_length=254)

    captcha = ReCaptchaField()

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


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    security_answer = forms.CharField(max_length=4000, required=True)

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
