from django.urls import path

from . import views

app_name = "survey"
urlpatterns = [
    path(
        "application-submitted/<int:process_pk>",
        views.DoYouWantToProvideFeedbackView.as_view(),
        name="application_submitted",
    ),
    path(
        "provide-feedback/",
        views.ProvideFeedbackView.as_view(),
        name="provide_generic_feedback",
    ),
    path(
        "provide-feedback/<int:process_pk>/",
        views.ProvideApplicationFeedbackView.as_view(),
        name="provide_application_feedback",
    ),
]
