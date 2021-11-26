from django.urls import path

from . import views

app_name = "cat"
urlpatterns = [
    path("", views.CATListView.as_view(), name="list"),
    path("create/", views.create, name="create"),
    path("edit/<int:cat_pk>/", views.CATEditView.as_view(), name="edit"),
    path("edit/<int:cat_pk>/archive/", views.CATArchiveView.as_view(), name="archive"),
    path("edit/<int:cat_pk>/restore/", views.CATRestoreView.as_view(), name="restore"),
    path("edit/<int:cat_pk>/<str:step>/", views.CATEditView.as_view(), name="edit-step"),
    path("view/<int:cat_pk>/", views.CATReadOnlyView.as_view(), name="view"),
    path("view/<int:cat_pk>/<str:step>/", views.CATReadOnlyView.as_view(), name="view-step"),
]
