from django.urls import path
from django.contrib.auth import views as auth_view

from . import views

urlpatterns = [
    path(
        '',
        auth_view.LoginView.as_view(template_name='icms/login.html'),
        name='login'),
    path('logout', auth_view.LogoutView.as_view(), name='logout'),
    path('home', views.home, name='home'),
    path('register', views.register, name='register'),
    path('change_password', views.change_password, name='change_password'),
]
