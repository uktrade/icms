from django.urls import path

from .views import UserFeedbackView

app_name = "survey"
urlpatterns = [
    path(
        "<int:process_pk>/",
        UserFeedbackView.as_view(),
        name="user-feedback",
    )
]
