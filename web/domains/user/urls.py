from django.urls import include, path

from . import views

urlpatterns = [
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
    # Admin Views to view users in ICMS.
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
