import datetime

from django.forms import ValidationError


def validate_email_confirmation(form):
    email = form.cleaned_data.get("email", None)
    if email != form.cleaned_data.get("confirm_email", None):
        raise ValidationError("This email address doesn't match the one above ")

    return email


def validate_security_answer(form):
    answer = form.cleaned_data.get("security_answer", None)
    if answer != form.user.security_answer:
        raise ValidationError(
            (
                "Your security answer didn't match the one you gave us when\
            you created your account"
            )
        )

    return answer


def validate_security_answer_confirmation(form):
    answer = form.cleaned_data.get("security_answer", None)
    repeat = form.cleaned_data.get("security_answer_repeat", None)
    if answer != repeat:
        raise ValidationError("Security answers do not match.")

    return repeat


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


def validate_manual_address(form):
    address = form.cleaned_data.get("address", "").upper()
    country = form.cleaned_data.get("country", "").upper()
    if country not in address:
        raise ValidationError("Country name must be included in the address.")

    return address
