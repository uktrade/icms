from django.contrib.auth.views import LogoutView
from django.urls import include, path, register_converter

from viewflow.flow.viewset import FlowViewSet
from web.domains.application._import import views as imp_app_views
from web.domains.commodity import views as commodity_views
from web.domains.constabulary import views as constabulary_views
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
from web.domains.user.views import (UsersListView, current_user_details,
                                    user_details)
from web.domains.workbasket.views import take_ownership, workbasket

from . import converters
from .auth import views as auth_views
from web.domains.case.access.views import (AccessRequestCreatedView,
                                           AccessRequestFirView,
                                           LinkImporterView, LinkExporterView)
from web.domains.mailshot.views import MailshotListView

from .flows import AccessRequestFlow
from .views import home

register_converter(converters.NegativeIntConverter, 'negint')

access_request_urls = FlowViewSet(AccessRequestFlow).urls

urlpatterns = [
    path('', auth_views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', auth_views.register, name='register'),
    path('reset-password/', auth_views.reset_password, name='reset-password'),
    path('home/', home, name='home'),
    path('set-password/', auth_views.set_password, name='set-password'),
    path('user/password/', auth_views.change_password, name='change-password'),
    path('user/', current_user_details, name='current-user-details'),
    path('users/', UsersListView.as_view(), name='users-list'),
    path('users/<negint:pk>/', user_details, name='user-details'),
    path('users/<negint:pk>/edit/', user_details),
    path('workbasket/', workbasket, name='workbasket'),

    # Template Management
    path('template/', TemplateListView.as_view(), name='template-list'),

    # Teams Management
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/edit/', TeamEditView.as_view(), name='team-edit'),

    # Constabularies Management
    path('constabulary/',
         constabulary_views.ConstabularyListView.as_view(),
         name='constabulary-list'),
    path('constabulary/<int:pk>/',
         constabulary_views.ConstabularyDetailView.as_view(),
         name='constabulary-detail'),
    path('constabulary/new/',
         constabulary_views.ConstabularyCreateView.as_view(),
         name='constabulary-new'),
    path('constabulary/<int:pk>/edit/',
         constabulary_views.ConstabularyEditView.as_view(),
         name='constabulary-edit'),

    # Commodities Management
    path('commodity/',
         commodity_views.CommodityListView.as_view(),
         name='commodity-list'),
    path('commodity/<int:pk>/',
         commodity_views.CommodityDetailView.as_view(),
         name='commodity-detail'),
    path('commodity/<int:pk>/edit/',
         commodity_views.CommodityEditView.as_view(),
         name='commodity-edit'),
    path('commodity/new/',
         commodity_views.CommodityCreateView.as_view(),
         name='commodity-new'),

    # Commodity Groups Management
    path('commodity/group/',
         commodity_views.CommodityGroupListView.as_view(),
         name='commodity-group-list'),
    path('commodity/group/<int:pk>/',
         commodity_views.CommodityGroupDetailView.as_view(),
         name='commodity-group-detail'),
    path('commodity/group/<int:pk>/edit/',
         commodity_views.CommodityGroupEditView.as_view(),
         name='commodity-group-edit'),
    path('commodity/group/new/',
         commodity_views.CommodityGroupCreateView.as_view(),
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
    path('access/<process_id>/fir',
         AccessRequestFirView.as_view(),
         name="access_request_fir_list"),
    path('access/', include(access_request_urls)),
    path('access/<process_id>/review_request/<task_id>/link-importer/',
         LinkImporterView.as_view(),
         name="link-importer"),
    path('access/<process_id>/review_request/<task_id>/link-exporter/',
         LinkExporterView.as_view(),
         name="link-exporter"),
    path("access-created/",
         AccessRequestCreatedView.as_view(),
         name="access_request_created"),
    path("take-ownership/<process_id>/", take_ownership,
         name="take_ownership"),

    # Import Application
    path('import/apply/',
         imp_app_views.ImportApplicationCreateView.as_view(),
         name='import_application_new'),

    # Mailshots
    path('mailshots/', MailshotListView.as_view(), name='mailshot-list'),


]
