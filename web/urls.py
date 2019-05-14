from .views import views
from .flows import flows
from django.urls import path, re_path, include
from django.views import generic
from django.contrib.auth import views as auth_view
from viewflow.flow.viewset import FlowViewSet

urlpatterns = [
    path(
        '',
        auth_view.LoginView.as_view(
            template_name='web/login.html', redirect_authenticated_user=True),
        name='login'),
    path('logout/', auth_view.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('set-password/', views.set_password, name='set-password'),
    path('workbasket/', views.workbasket, name='workbasket'),
    path('user/', views.user_details, name='user-details'),
    path('user/password/', views.change_password, name='change-password'),

    # Template Management
    path('template/', views.templates, name='template-list'),

    # Access Request
    path(
        'access/',
        generic.RedirectView.as_view(url='request', permanent=False),
        name='request-access'),
    re_path(r'^access/', include(FlowViewSet(flows.AccessRequestFlow).urls)),
]
