from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import redirect, render
from web.auth.decorators import require_registered
from web.domains.user import PersonalEmail, User
from web.notify import notify

from .forms import (CaptchaForm, LoginForm, PasswordChangeForm,
                    RegistrationForm, ResetPasswordForm,
                    ResetPasswordSecondForm)


class LoginView(LoginView):
    form_class = LoginForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    authentication_form = LoginForm


@user_passes_test(lambda u: u.is_anonymous, login_url='home')
@transaction.atomic
def register(request):
    """
  An atomic transaction to save user information and send notifications
  When an unexpected error occurs the whole transaction is rolled back
  """
    # Handle security question
    data = request.POST.copy() if request.POST else None
    selected = request.POST.get('security_question_list', None)
    if selected and selected != RegistrationForm.OWN_QUESTION:
        data['security_question'] = selected
    form = RegistrationForm(data)
    captcha_form = CaptchaForm(request.POST or None)
    if form.is_valid() and captcha_form.is_valid():
        user = form.instance
        temp_pass = user.set_temp_password()
        user.username = user.email
        user.save()
        user.phone_numbers.create(phone=form.cleaned_data['telephone_number'])
        PersonalEmail(user=user,
                      email=user.email,
                      is_primary=True,
                      portal_notifications=True).save()
        login(request, user)
        notify.register(user, temp_pass)
        return redirect('set-password')

    return render(request, 'auth/registration.html', {
        'form': form,
        'captcha_form': captcha_form
    })


def update_password(request):
    form = PasswordChangeForm(
        request.user,
        request.POST or None,
        initial={'security_question': request.user.security_question})

    if form.is_valid():
        user = form.save(commit=False)
        user.password_disposition = User.FULL
        user.save()
        update_session_auth_hash(request, user)  # keep user logged in

    return form


@user_passes_test(lambda u: u.is_anonymous, login_url='home')
def reset_password(request):
    action = request.POST.get('action') if request.POST else None
    login_id = request.POST.get('login_id', None)

    if action == 'reset_password':
        user = User.objects.get(username=login_id)
        form = ResetPasswordSecondForm(user, request.POST or None)
        if form.is_valid():
            temp_pass = user.set_temp_password()
            user.save()
            notify.register(user, temp_pass)
            return render(request,
                          'auth/reset-password/reset-password-success.html')

        return render(request, 'auth/reset-password/reset-password-2.html', {
            'form': form,
            'login_id': login_id
        })

    form = ResetPasswordForm(request.POST or None)
    if form.is_valid():
        try:
            user = User.objects.get(
                username=form.cleaned_data.get('login_id', ''))
            form = ResetPasswordSecondForm(user)
            return render(request, 'auth/reset-password/reset-password-2.html',
                          {
                              'form': form,
                              'login_id': user.username
                          })
        except ObjectDoesNotExist:
            form.add_error(None, 'Invalid login id')

    return render(request, 'auth/reset-password/reset-password-1.html',
                  {'form': form})


@login_required
def set_password(request):
    form = update_password(request)

    if form.is_valid():
        return redirect('home')

    return render(request, 'auth/set-password.html', {'form': form})


@require_registered
def change_password(request):
    form = update_password(request)

    return render(request, 'web/domains/user/password.html', {'form': form})
