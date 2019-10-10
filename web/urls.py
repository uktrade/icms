from django.contrib.auth.views import LogoutView
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from viewflow.flow.viewset import FlowViewSet
from web.domains.case.access.views import AccessRequestFlow
from web.domains.commodity.views import (
    CommodityCreateView, CommodityEditView, CommodityGroupCreateView,
    CommodityGroupEditView, CommodityGroupListView, CommodityListView)
from web.domains.constabulary.views import (ConstabularyCreateView,
                                            ConstabularyEditView,
                                            ConstabularyListView)

from web.domains.user.views import (UsersListView)

from web.domains.country.views import (
    CountryCreateView, CountryEditView, CountryGroupCreateView,
    CountryGroupEditView, CountryGroupView, CountryListView,
    CountryTranslationCreateUpdateView, CountryTranslationSetEditView,
    CountryTranslationSetListView)
from web.domains.exporter.views import (ExporterCreateView, ExporterDetailView,
                                        ExporterEditView, ExporterListView)
from web.domains.firearms.views import (ObsoleteCalibreGroupCreateView,
                                        ObsoleteCalibreGroupDetailView,
                                        ObsoleteCalibreGroupEditView,
                                        ObsoleteCalibreListView)
from web.domains.importer.views import (ImporterCreateView, ImporterDetailView,
                                        ImporterEditView, ImporterListView)
from web.domains.legislation.views import (ProductLegislationCreateView,
                                           ProductLegislationDetailView,
                                           ProductLegislationListView,
                                           ProductLegislationUpdateView)
from web.domains.team.views import TeamEditView, TeamListView
from web.domains.template.views import TemplateListView
from web.domains.user.views import user_details
from web.domains.workbasket.views import workbasket

from .auth import views as auth_views
from .views import home

urlpatterns = [
    path('', auth_views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', auth_views.register, name='register'),
    path('reset-password/', auth_views.reset_password, name='reset-password'),
    path('home/', home, name='home'),
    path('set-password/', auth_views.set_password, name='set-password'),
    path('user/password/', auth_views.change_password, name='change-password'),
    path('user/', user_details, name='user-details'),
    path('users/', UsersListView.as_view(), name='users-list'),
    path('workbasket/', workbasket, name='workbasket'),

    # Template Management
    path('template/', TemplateListView.as_view(), name='template-list'),

    # Teams Management
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/edit/', TeamEditView.as_view(), name='team-edit'),

    # Constabularies Management
    path('constabulary/',
         ConstabularyListView.as_view(),
         name='constabulary-list'),
    path('constabulary/new/',
         ConstabularyCreateView.as_view(),
         name='constabulary-new'),
    path('constabulary/<int:pk>/edit/',
         ConstabularyEditView.as_view(),
         name='constabulary-edit'),

    # Commodities Management
    path('commodity/', CommodityListView.as_view(), name='commodity-list'),
    path('commodity/<int:pk>/edit/',
         CommodityEditView.as_view(),
         name='commodity-edit'),
    path('commodity/new/', CommodityCreateView.as_view(),
         name='commodity-new'),

    # Commodity Groups Management
    path('commodity/group/',
         CommodityGroupListView.as_view(),
         name='commodity-group-list'),
    path('commodity/group/<int:pk>/edit/',
         CommodityGroupEditView.as_view(),
         name='commodity-group-edit'),
    path('commodity/group/new/',
         CommodityGroupCreateView.as_view(),
         name='commodity-group-new'),

    # Countries management
    path('country/', CountryListView.as_view(), name='country-list'),
    path('country/new/', CountryCreateView.as_view(), name='country-new'),
    path('country/<int:pk>/edit/',
         CountryEditView.as_view(),
         name='country-edit'),

    # Country Groups Management
    path('country/groups/',
         CountryGroupView.as_view(),
         name='country-group-view'),
    path('country/groups/<int:pk>/',
         CountryGroupView.as_view(),
         name='country-group-view'),
    path('country/groups/new/',
         CountryGroupCreateView.as_view(),
         name='country-group-new'),
    path('country/groups/<int:pk>/edit/',
         CountryGroupEditView.as_view(),
         name='country-group-edit'),

    # Coutry translation sets
    path('country/translations/',
         CountryTranslationSetListView.as_view(),
         name='country-translation-set-list'),
    path('country/translations/<int:pk>/edit/',
         CountryTranslationSetEditView.as_view(),
         name='country-translation-set-edit'),
    path('country/translations/<int:set_pk>/edit/<int:country_pk>',
         CountryTranslationCreateUpdateView.as_view(),
         name='country-translation-edit'),

    # Product legislation
    path('product-legislation/',
         ProductLegislationListView.as_view(),
         name='product-legislation-list'),
    path('product-legislation/new/',
         ProductLegislationCreateView.as_view(),
         name='product-legislation-new'),
    path('product-legislation/<int:pk>/',
         ProductLegislationDetailView.as_view(),
         name='product-legislation-detail'),
    path('product-legislation/<int:pk>/edit/',
         ProductLegislationUpdateView.as_view(),
         name='product-legislation-edit'),

    #  Obsolete Calibres Management
    path('obsolete-calibre/',
         ObsoleteCalibreListView.as_view(),
         name='obsolete-calibre-list'),
    path('obsolete-calibre/new',
         ObsoleteCalibreGroupCreateView.as_view(),
         name='obsolete-calibre-new'),
    path('obsolete-calibre/<int:pk>/edit/',
         ObsoleteCalibreGroupEditView.as_view(),
         name='obsolete-calibre-edit'),
    path('obsolete-calibre/<int:pk>/',
         ObsoleteCalibreGroupDetailView.as_view(),
         name='obsolete-calibre-view'),

    # Importer
    path('importer/', ImporterListView.as_view(), name='importer-list'),
    path('importer/<int:pk>/edit/',
         ImporterEditView.as_view(),
         name='importer-edit'),
    path('importer/new/', ImporterCreateView.as_view(), name='importer-new'),
    path('importer/<int:pk>/',
         ImporterDetailView.as_view(),
         name='importer-view'),

    # Importer Agents
    path('importer/<int:importer_id>/agent/<int:pk>/edit',
         ImporterEditView.as_view(),
         name='importer-agent-edit'),
    path('importer/<int:importer_id>/agent/new/',
         ImporterCreateView.as_view(),
         name='importer-agent-new'),

    # Exporter
    path('exporter/', ExporterListView.as_view(), name='exporter-list'),
    path('exporter/<int:pk>/edit/',
         ExporterEditView.as_view(),
         name='exporter-edit'),
    path('exporter/new/', ExporterCreateView.as_view(), name='exporter-new'),
    path('exporter/<int:pk>/',
         ExporterDetailView.as_view(),
         name='exporter-view'),

    # Access Request
    path('access/',
         RedirectView.as_view(url='request', permanent=False),
         name='request-access'),
    re_path(r'^access/', include(FlowViewSet(AccessRequestFlow).urls)),
]
