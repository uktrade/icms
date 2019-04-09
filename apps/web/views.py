from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.conf import settings


def index(request):
    return render(request, 'icms/login.html')


@login_required
def home(request):
    return render(request, 'icms/home.html')
