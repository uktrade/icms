from django.http import HttpResponse, HttpResponseForbidden
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.conf import settings


def index(request):
    template = loader.get_template('icms/index.html')
    return HttpResponse(template.render({}, request))


@login_required
def home(request):
    template = loader.get_template('icms/home.html')
    return HttpResponse(template.render({}, request))


def auth(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('home')
    else:
        return HttpResponseForbidden(
            loader.get_template('icms/index.html').render(
                {'login_error': True}, request))


def log_out(request):
    logout(request)
    return redirect(settings.LOGIN_URL)
