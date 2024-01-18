from django.urls import path

from . import views

app_name = "country"

urlpatterns = [
    # Countries management
    path("", views.CountryListView.as_view(), name="list"),
    path("new/", views.CountryCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.CountryEditView.as_view(), name="edit"),
    #
    # Country Groups Management
    path("groups/", views.CountryGroupListView.as_view(), name="group-list"),
    path("groups/add/", views.CountryGroupCreateView.as_view(), name="group-add"),
    path("groups/<int:pk>/", views.CountryGroupView.as_view(), name="group-view"),
    path("groups/<int:pk>/edit/", views.CountryGroupEditView.as_view(), name="group-edit"),
    #
    # Country translation sets
    path(
        "translations/",
        views.CountryTranslationSetListView.as_view(),
        name="translation-set-list",
    ),
    path(
        "translations/<int:pk>/edit/",
        views.CountryTranslationSetEditView.as_view(),
        name="translation-set-edit",
    ),
    path(
        "translations/<int:set_pk>/edit/<int:country_pk>/",
        views.CountryTranslationCreateUpdateView.as_view(),
        name="translation-edit",
    ),
]
