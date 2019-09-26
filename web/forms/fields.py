from django import forms
#from .widgets import (TextInput, EmailInput, DateInput, Display)
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget
from phonenumber_field.formfields import PhoneNumberField

#  class CharField(forms.CharField):
#      widget = TextInput
#
#
#  class DateField(forms.DateField):
#      widget = DateInput
#
#
#  class BooleanField(forms.BooleanField):
#      pass
#
#
#  class EmailField(forms.EmailField):
#      widget = EmailInput
#
#
#  class ChoiceField(forms.ChoiceField):
#      pass
#
#
#  class ModelChoiceField(forms.ModelChoiceField):
#      pass
#
#
#  class DisplayField(forms.Field):
#      widget = Display
#
#      def __init__(self, *args, **kwargs):
#          kwargs.pop('disabled', None)
#          super(DisplayField, self).__init__(*args, disabled=True, **kwargs)
#
#
#  class PhoneNumberField(PhoneNumberField):
#      widget = PhoneNumberInternationalFallbackWidget
#      max_length = 60
#      help_text = "Customary input formats:\n\
#      \n\
#      - FOR United Kingdom:\n\
#      FORMAT: STD NUMBER\n\
#      U.Kingdom: 020 12345678\n\
#      - FOR International:\n\
#      FORMAT: +CC (NDD)STD NUMBER\n\
#      Netherlands: +31 (0)20 12345678\n\
#      Hungary: +36 (06)1 12345678\n\
#      U.Kingdom: +44 (0)20 12345678\n\
#      - FOR International without NDD:\n\
#      FORMAT: +CC STD NUMBER<br>Norway: +47 123 4568900\n\
#      Spain: +34 911 12345678\n\
#      America: +1 123 4568900"
