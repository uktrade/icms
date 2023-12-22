from django.urls import path

from .views import (
    SignatureCreateView,
    SignatureDetailView,
    SignatureListView,
    SignatureSetActiveView,
)

urlpatterns = [
    path("", SignatureListView.as_view(), name="signature-list"),
    path("create/", SignatureCreateView.as_view(), name="signature-create"),
    path("<int:signature_pk>/", SignatureDetailView.as_view(), name="signature-view"),
    path(
        "<int:signature_pk>/set-active/",
        SignatureSetActiveView.as_view(),
        name="signature-set-active",
    ),
]
