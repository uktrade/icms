from django.urls import path
from django.contrib.auth import views as auth_view

from . import views
from .forms import LoginForm

urlpatterns = [
    path(
        '',
        auth_view.LoginView.as_view(
            template_name='icms/login.html', authentication_form=LoginForm),
        name='login'),
    path('logout', auth_view.LogoutView.as_view(), name='logout'),
    path('home', views.home, name='home'),
]
