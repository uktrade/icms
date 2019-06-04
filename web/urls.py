from .views import views
from .flows import flows
from django.urls import path, re_path, include
from django.views import generic
from django.contrib.auth import views as auth_view
from viewflow.flow.viewset import FlowViewSet

urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('logout/', auth_view.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('set-password/', views.set_password, name='set-password'),
    path('workbasket/', views.workbasket, name='workbasket'),
    path('user/', views.user_details, name='user-details'),
    path('user/password/', views.change_password, name='change-password'),

    # Template Management
    path('template/', views.templates, name='template-list'),
    # Teams Management
    path('teams/', views.teams, name='team-list'),

    # Constabularies Management
    path('constabulary', views.constabularies, name='constabulary-list'),

    # Portal Dashboard for outbound emails
    path('portal/dashboard', views.outbound_emails, name='outbound-emails'),

    # Access Request
    path(
        'access/',
        generic.RedirectView.as_view(url='request', permanent=False),
        name='request-access'),
    re_path(r'^access/', include(FlowViewSet(flows.AccessRequestFlow).urls)),
]
