from django.urls import path

from .views import AuthCallbackView, AuthView, OIDCBackChannelLogoutView

app_name = "one_login"
urlpatterns = [
    path("login/", AuthView.as_view(), name="login"),
    path("callback/", AuthCallbackView.as_view(), name="callback"),
    path("back-channel-logout/", OIDCBackChannelLogoutView.as_view(), name="back-channel-logout"),
]
