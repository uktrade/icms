from django.forms import ValidationError


def validate_security_answer(form):
    answer = form.cleaned_data['security_answer']
    if answer != form.user.security_answer:
        raise ValidationError(
            ("Your security answer didn't match the one you gave us when\
            you created your account"))

    return answer


def validate_security_answer_confirmation(form):
    answer = form.cleaned_data['security_answer']
    repeat = form.cleaned_data['security_answer_repeat']
    if answer != repeat:
        raise ValidationError('Security answers to not match.')
