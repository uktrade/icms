from . import views, flows
from django.urls import path, re_path, include
from django.views import generic
from django.contrib.auth import views as auth_view
from viewflow.flow.viewset import FlowViewSet

urlpatterns = [
    path(
        '',
        auth_view.LoginView.as_view(template_name='icms/public/login.html'),
        name='login'),
    path('logout/', auth_view.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('change_password/', views.change_password, name='change_password'),
    path(
        'access/',
        generic.RedirectView.as_view(url='request', permanent=False),
        name='request_access'),
    re_path(r'^access/', include(FlowViewSet(flows.AccessRequestFlow).urls)),
]
