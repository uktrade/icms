from . import views as view
from .views import views
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
    path('template/', view.TemplateListView.as_view(), name='template-list'),
    path('template/<int:pk>', view.TemplateListView.as_view(), name='template-list'),
    # Teams Management
    path('teams/', view.TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/edit/', view.TeamEditView.as_view(), name='team-edit'),

    # Constabularies Management
    path(
        'constabulary/',
        view.ConstabularyListView.as_view(),
        name='constabulary-list'),
    path(
        'constabulary/<int:pk>/edit/',
        view.ConstabularyEditView.as_view(),
        name='constabulary-edit'),
    path(
        'constabulary/new/',
        view.ConstabularyCreateView.as_view(),
        name='constabulary-new'),

    # Commodities Management
    path('commodities/', view.CommodityListView.as_view(), name='commodity-list'),
    path(
        'commodities/<int:pk>/edit/',
        view.CommodityEditView.as_view(),
        name='commodity-edit'),
    path(
        'commodities/new/',
        view.CommodityCreateView.as_view(),
        name='commodity-new'),

    # Commodity Groups Management
    path(
        'commodity-groups/',
        view.CommodityGroupListView.as_view(),
        name='commodity-groups'),
    path(
        'commodity-groups/<int:pk>/edit/',
        view.CommodityGroupEditView.as_view(),
        name='commodity-group-edit'),
    path(
        'commodity-groups/new/',
        view.CommodityGroupCreateView.as_view(),
        name='commodity-group-new'),

    # Countries management
    path('country/', view.CountryListView.as_view(), name='country-list'),
    path(
        'country/<int:pk>/edit/',
        view.CountryEditView.as_view(),
        name='country-edit'),
    path('country/new/', view.CountryCreateView.as_view(), name='country-new'),

    # Country Groups Management
    path(
        'country/groups/',
        view.CountryGroupView.as_view(),
        name='country-group-view'
    ),
    path(
        'country/groups/<int:pk>/',
        view.CountryGroupView.as_view(),
        name='country-group-view'
    ),
    path(
        'country/groups/<int:pk>/edit/',
        view.CountryGroupEditView.as_view(),
        name='country-group-edit'
    ),
    path(
        'country/groups/new/',
        view.CountryGroupCreateView.as_view(),
        name='country-group-view'
    ),

    # Coutry translation sets
    path(
        'country/translations/',
        view.CountryTranslationListView.as_view(),
        name='country-translation-list'),

    # Product legislation
    path(
        'product-legislation/',
        view.ProductLegislationListView.as_view(),
        name='product-legislation-list'),

    path(
        'product-legislation/<int:pk>/',
        view.ProductLegislationDetailView.as_view(),
        name='product-legislation-detail'),

    path(
        'product-legislation/<int:pk>/edit/',
        view.ProductLegislationEditView.as_view(),
        name='product-legislation-edit'),

    path(
        'product-legislation/new/',
        view.ProductLegislationCreateView.as_view(),
        name='product-legislation-new'),

    #  Obsolete Calibres Management
    path(
        'obsolete-calibre/',
        view.ObsoleteCalibreListView.as_view(),
        name='obsolete-calibre-list'),


    # Portal Dashboard for outbound emails
    path('portal/dashboard/', outbound_emails, name='outbound-emails'),

    # Access Request
    path(
        'access/',
        generic.RedirectView.as_view(url='request', permanent=False),
        name='request-access'),
    re_path(r'^access/', include(FlowViewSet(AccessRequestFlow).urls)),
]
