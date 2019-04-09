from django.urls import path
from django.contrib.auth import views as auth_view

from . import views

urlpatterns = [
    path(
        '',
        auth_view.LoginView.as_view(template_name='icms/login.html'),
        name='login'),
    path('logout', views.log_out, name='logout'),
    path('home', views.home, name='home'),
]
