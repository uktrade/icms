from django.conf import settings
from django.urls import include, path

from . import views

public_urls = [
    path("welcome/", views.NewUserWelcomeView.as_view(), name="user-welcome"),
    path("welcome/clear/", views.ClearNewUserWelcomeView.as_view(), name="user-welcome-clear"),
    path("new-user/", views.NewUserUpdateView.as_view(), name="new-user-edit"),
    path(
        "<int:user_pk>/",
        include(
            [
                path("", views.UserUpdateView.as_view(), name="user-edit"),
                path(
                    "number/",
                    include(
                        [
                            path(
                                "add/",
                                views.UserCreateTelephoneView.as_view(),
                                name="user-number-add",
                            ),
                            path(
                                "<int:phonenumber_pk>/",
                                include(
                                    [
                                        path(
                                            "edit/",
                                            views.UserUpdateTelephoneView.as_view(),
                                            name="user-number-edit",
                                        ),
                                        path(
                                            "delete/",
                                            views.UserDeleteTelephoneView.as_view(),
                                            name="user-number-delete",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "email/",
                    include(
                        [
                            path(
                                "add/",
                                views.UserCreateEmailView.as_view(),
                                name="user-email-add",
                            ),
                            path(
                                "<int:email_pk>/",
                                include(
                                    [
                                        path(
                                            "edit/",
                                            views.UserUpdateEmailView.as_view(),
                                            name="user-email-edit",
                                        ),
                                        path(
                                            "delete/",
                                            views.UserDeleteEmailView.as_view(),
                                            name="user-email-delete",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]

private_urls = [
    path("users/", views.UsersListView.as_view(), name="users-list"),
    path("users/<int:user_pk>/", views.UserDetailView.as_view(), name="user-details"),
    path(
        "users/<int:user_pk>/reactivate/",
        views.UserReactivateFormView.as_view(),
        name="user-reactivate",
    ),
    path(
        "users/<int:user_pk>/deactivate/",
        views.UserDeactivateFormView.as_view(),
        name="user-deactivate",
    ),
]

if settings.INCLUDE_PRIVATE_URLS:
    urlpatterns = public_urls + private_urls
else:
    urlpatterns = public_urls


if settings.APP_ENV in ("local", "dev", "uat", "staging"):
    urlpatterns.extend(
        [
            # One Login Test User urls
            path(
                "setup-one-login-test-accounts/",
                views.OneLoginTestAccountsCreateFormView.as_view(),
                name="one-login-test-accounts-create",
            ),
            path(
                "one-login-test-accounts/<int:user_pk>/",
                views.OneLoginTestAccountsDetailView.as_view(),
                name="one-login-test-accounts-detail",
            ),
        ]
    )
