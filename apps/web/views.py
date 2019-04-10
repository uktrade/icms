import random
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, PasswordChangeForm
from . import notify

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'icms/login.html')


@login_required
def home(request):
    return render(request, 'icms/home.html')


@login_required
def change_password(request):
    logger.debug('Receieved change password requuest %r', request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            logger.debug('Form is valid')
            user = form.save()
            logger.debug('Saved user')
            update_session_auth_hash(request, user)
            return redirect('change_password')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'icms/change_password.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
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
        form = RegistrationForm()

    return render(request, 'icms/registration.html', {'form': form})
