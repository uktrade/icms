import random
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.db import transaction
from web.views import forms
from web.notify import notify
from web.auth.decorators import require_registered
from viewflow.decorators import flow_start_view
from web import models
from . import filters

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'web/login.html')


@require_registered
def home(request):
    return render(request, 'web/home.html')


@require_registered
@flow_start_view
def request_access(request):
    request.activation.prepare(request.POST or None, user=request.user)
    form = forms.AccessRequestForm(request.POST or None)
    if form.is_valid():
        access_request = form.instance
        access_request.user = request.user
        access_request.save()
        request.activation.process.access_request = access_request
        request.activation.done()
        return render(request, 'web/request-access-success.html')

    return render(request, 'web/request-access.html', {
        'form': form,
        'activation': request.activation
    })


def update_password(request):
    form = forms.PasswordChangeForm(
        request.user,
        request.POST or None,
        initial={'security_question': request.user.security_question})

    if form.is_valid():
        user = form.save(commit=False)
        user.register_complete = True
        user.save()
        update_session_auth_hash(request, user)  # keep user logged in

    return form


@login_required
def set_password(request):
    form = update_password(request)

    if form.is_valid():
        return redirect('home')

    return render(request, 'web/set-password.html', {'form': form})


@require_registered
def change_password(request):
    form = update_password(request)

    return render(request, 'web/user/password.html', {'form': form})


@transaction.atomic
def register(request):
    """
    An atomic transaction to save user information and send notifications
    When an unexpected error occurs the whole transaction is rolled back
    """
    form = forms.RegistrationForm(request.POST or None)
    captcha_form = forms.CaptchaForm(request.POST or None)
    if form.is_valid() and captcha_form.is_valid():
        user = form.instance
        temp_pass = random.randint(1000, 1000000)
        user.set_password(temp_pass)
        user.username = user.email
        user.save()
        user.phone_numbers.create(phone=form.cleaned_data['telephone_number'])
        email = models.EmailAddress.objects.create(
            email=user.email, portal_notifications=True)
        models.PersonalEmail(
            user=user, email_address=email, is_primary=True).save()
        notify.register(request, user, temp_pass)
        login(request, user)
        return redirect('set-password')

    return render(request, 'web/registration.html', {
        'form': form,
        'captcha_form': captcha_form
    })


@require_registered
def workbasket(request):
    process = models.AccessRequestProcess.objects.owned_process(request.user)
    return render(request, 'web/workbasket.html', {'process_list': process})


@require_registered
def templates(request):
    filter = filters.TemplatesFilter(
        request.GET, queryset=models.Template.objects.all())
    return render(request, 'web/template/list.html', {'filter': filter})


@require_registered
def outbound_emails(request):
    filter = filters.OutboundEmailsFilter(
        request.GET,
        queryset=models.OutboundEmail.objects.all().prefetch_related(
            'attachments'))
    return render(request, 'web/portal/outbound-emails.html',
                  {'filter': filter})


@require_registered
def user_details(request):
    form = forms.UserDetailsUpdateForm(
        request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success('Central contact details have been saved.')

    return render(request, 'web/user/details.html', {'form': form})


class LoginView(auth_views.LoginView):
    form_class = forms.LoginForm
    template_name = 'web/login.html'
    redirect_authenticated_user = True
