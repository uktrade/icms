import datetime

from django.forms import ValidationError


def validate_email_confirmation(form):
    email = form.cleaned_data.get("email", None)
    if email != form.cleaned_data.get("confirm_email", None):
        raise ValidationError("This email address doesn't match the one above ")

    return email


def validate_date_of_birth_not_in_future(form):
    date_of_birth = form.cleaned_data.get("date_of_birth", None)
    if date_of_birth >= datetime.date.today():
        raise ValidationError("Date of birth can't be in the future")

    return date_of_birth


def validate_date_of_birth(form):
    date_of_birth = form.cleaned_data.get("date_of_birth", None)
    if date_of_birth != form.user.date_of_birth:
        raise ValidationError("Birthday does not match")

    return date_of_birth
