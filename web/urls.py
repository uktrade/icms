from .views import views
from .views import (TemplateListView, ConstabularyListView,
                    ConstabularyEditView, ConstabularyCreateView,
                    CommodityListView, CommodityEditView, CommodityCreateView,
                    CommodityGroupListView, CommodityGroupEditView,
                    CommodityGroupCreateView, TeamListView, TeamEditView)
from .views.dashboard import outbound_emails
from .views.access_request import AccessRequestFlow
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
    path('template/', TemplateListView.as_view(), name='template-list'),
    # Teams Management
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/edit/', TeamEditView.as_view(), name='team-edit'),

    # Constabularies Management
    path(
        'constabulary/',
        ConstabularyListView.as_view(),
        name='constabulary-list'),
    path(
        'constabulary/<int:pk>/edit/',
        ConstabularyEditView.as_view(),
        name='constabulary-edit'),
    path(
        'constabulary/new/',
        ConstabularyCreateView.as_view(),
        name='constabulary-new'),

    # Commodities Management
    path('commodities/', CommodityListView.as_view(), name='commodity-list'),
    path(
        'commodities/<int:pk>/edit/',
        CommodityEditView.as_view(),
        name='commodity-edit'),
    path(
        'commodities/new/',
        CommodityCreateView.as_view(),
        name='commodity-new'),

    # Commodity Groups Management
    path(
        'commodity-groups/',
        CommodityGroupListView.as_view(),
        name='commodity-groups'),
    path(
        'commodity-groups/<int:pk>/edit/',
        CommodityGroupEditView.as_view(),
        name='commodity-group-edit'),
    path(
        'commodity-groups/new/',
        CommodityGroupCreateView.as_view(),
        name='commodity-group-new'),
    path('people/', views.search_people, name='search_people'),

    # Portal Dashboard for outbound emails
    path('portal/dashboard/', outbound_emails, name='outbound-emails'),

    # Access Request
    path(
        'access/',
        generic.RedirectView.as_view(url='request', permanent=False),
        name='request-access'),
    re_path(r'^access/', include(FlowViewSet(AccessRequestFlow).urls)),
]
