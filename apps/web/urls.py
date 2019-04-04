from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.auth, name='auth'),
    path('logout', views.log_out, name='logout'),
    path('home', views.home, name='home'),
]
