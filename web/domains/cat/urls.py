from django.urls import path

from . import views

app_name = "cat"
urlpatterns = [
    path("", views.CATListView.as_view(), name="list"),
    path("create/", views.create, name="create"),
    path("edit/<int:cat_pk>/", views.CATEditView.as_view(), name="edit"),
    path("edit/<int:cat_pk>/archive/", views.CATArchiveView.as_view(), name="archive"),
    path("edit/<int:cat_pk>/restore/", views.CATRestoreView.as_view(), name="restore"),
    path("edit/<int:cat_pk>/step/<str:step>/", views.CATEditView.as_view(), name="edit-step"),
    path(
        "edit/<int:cat_pk>/step/<str:step>/step_pk/<int:step_pk>/",
        views.CATEditView.as_view(),
        name="edit-step-related",
    ),
    path("view/<int:cat_pk>/", views.CATReadOnlyView.as_view(), name="view"),
    path("view/<int:cat_pk>/step/<str:step>/", views.CATReadOnlyView.as_view(), name="view-step"),
    path(
        "view/<int:cat_pk>/step/<str:step>/step_pk/<int:step_pk>/",
        views.CATReadOnlyView.as_view(),
        name="view-step-related",
    ),
    # CFS Specific Views:
    path(
        "edit/<int:cat_pk>/add-schedule/",
        views.CFSScheduleTemplateAddView.as_view(),
        name="cfs-schedule-add",
    ),
    path(
        "edit/<int:cat_pk>/schedule_template/<int:schedule_template_pk>/copy-schedule/",
        views.CFSScheduleTemplateCopyView.as_view(),
        name="cfs-schedule-copy",
    ),
    path(
        "edit/<int:cat_pk>/schedule_template/<int:schedule_template_pk>/delete-schedule/",
        views.CFSScheduleTemplateDeleteView.as_view(),
        name="cfs-schedule-delete",
    ),
    path(
        "edit/<int:cat_pk>/schedule_template/<int:schedule_template_pk>/cfs-manufacturer-update/",
        views.CFSManufacturerUpdateView.as_view(),
        name="cfs-manufacturer-update",
    ),
    path(
        "edit/<int:cat_pk>/schedule_template/<int:schedule_template_pk>/cfs-manufacturer-delete/",
        views.CFSManufacturerDeleteView.as_view(),
        name="cfs-manufacturer-delete",
    ),
]
