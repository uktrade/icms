import datetime
from django.forms import ValidationError


def validate_security_answer(form):
    answer = form.cleaned_data.get('security_answer', None)
    if answer != form.user.security_answer:
        raise ValidationError(
            ("Your security answer didn't match the one you gave us when\
            you created your account"))

    return answer


def validate_security_answer_confirmation(form):
    answer = form.cleaned_data.get('security_answer', None)
    repeat = form.cleaned_data.get('security_answer_repeat', None)
    if answer != repeat:
        raise ValidationError('Security answers do not match.')

    return repeat


def validate_date_of_birth(form):
    date_of_birth = form.cleaned_data.get('date_of_birth', None)
    if date_of_birth >= datetime.date.today():
        raise ValidationError("Date of birth can't be in the future")

    return date_of_birth
