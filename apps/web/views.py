import random
import logging
from . import forms, notify
from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from viewflow.decorators import flow_start_view

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'icms/public/login.html')


@login_required
def home(request):
    return render(request, 'icms/internal/home.html')


@login_required
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
        return render(request, 'icms/internal/request-access-success.html')

    return render(request, 'icms/internal/request-access.html', {
        'form': form,
        'activation': request.activation
    })


@login_required
def change_password(request):
    logger.debug('Receieved change password requuest %r', request.user)
    if request.method == 'POST':
        form = forms.PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            logger.debug('Form is valid')
            user = form.save()
            logger.debug('Saved user')
            update_session_auth_hash(request, user)
            return redirect('change_password')
    else:
        form = forms.PasswordChangeForm(request.user)

    return render(request, 'icms/internal/change_password.html',
                  {'form': form})


def register(request):
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            logger.debug('Form is valid')
            user = form.instance
            temp_pass = random.randint(1000, 1000000)
            user.set_password(temp_pass)
            user.username = user.email
            user.save()
            notify.register(user, temp_pass)
            login(request, user)
            return redirect('change_password')
    else:
        logger.debug('Loading registration form')
        form = forms.RegistrationForm()

    return render(request, 'icms/public/registration.html', {'form': form})
