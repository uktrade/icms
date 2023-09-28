from django import forms


class NonLocalizedForm(forms.Form):
    date_field = forms.DateField()
    datetime_field = forms.DateTimeField()
    time_field = forms.TimeField()
    int_field = forms.IntegerField()
    float_field = forms.FloatField()
    decimal_field = forms.FloatField()
    split_date_time_field = forms.SplitDateTimeField()


class LocalizedForm(forms.Form):
    date_field = forms.DateField(localize=True)
    datetime_field = forms.DateTimeField(localize=True)
    time_field = forms.TimeField(localize=True)
    int_field = forms.IntegerField(localize=True)
    float_field = forms.FloatField(localize=True)
    decimal_field = forms.FloatField(localize=True)
    split_date_time_field = forms.SplitDateTimeField(localize=True)
