from . import views, flows
from django.urls import path, re_path, include
from django.views import generic
from django.contrib.auth import views as auth_view
from viewflow.flow.viewset import FlowViewSet
from viewflow.flow.views import AllProcessListView

urlpatterns = [
    path(
        '',
        auth_view.LoginView.as_view(
            template_name='icms/public/login.html',
            redirect_authenticated_user=True),
        name='login'),
    path('logout/', auth_view.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('change-password/', views.change_password, name='change-password'),
    path('set-password/', views.set_password, name='set-password'),
    path(
        'workbasket/',
        AllProcessListView.as_view(
            template_name='icms/internal/workbasket.html'),
        name='workbasket'),
    path(
        'access/',
        generic.RedirectView.as_view(url='request', permanent=False),
        name='request-access'),
    re_path(r'^access/', include(FlowViewSet(flows.AccessRequestFlow).urls)),
]
