from django.urls import include, path

from . import views

app_name = "export"


product_urls = [
    path("edit/", views.cfs_edit_product, name="cfs-schedule-edit-product"),
    path("delete/", views.cfs_delete_product, name="cfs-schedule-delete-product"),
    path("ingredient/add/", views.cfs_add_ingredient, name="cfs-schedule-add-ingredient"),
    path(
        "ingredient/<int:ingredient_pk>/",
        include(
            [
                path("edit/", views.cfs_edit_ingredient, name="cfs-schedule-edit-ingredient"),
                path("delete/", views.cfs_delete_ingredient, name="cfs-schedule-delete-ingredient"),
            ]
        ),
    ),
    path("product-type/add/", views.cfs_add_product_type, name="cfs-schedule-add-product-type"),
    path(
        "product-type/<int:product_type_pk>/",
        include(
            [
                path("edit/", views.cfs_edit_product_type, name="cfs-schedule-edit-product-type"),
                path(
                    "delete/",
                    views.cfs_delete_product_type,
                    name="cfs-schedule-delete-product-type",
                ),
            ]
        ),
    ),
]


schedule_urls = [
    path("edit/", views.cfs_edit_schedule, name="cfs-schedule-edit"),
    path("delete/", views.cfs_delete_schedule, name="cfs-schedule-delete"),
    path("set-manufacturer/", views.cfs_set_manufacturer, name="cfs-schedule-set-manufacturer"),
    path(
        "manufacturer-address/delete",
        views.cfs_delete_manufacturer,
        name="cfs-schedule-delete-manufacturer",
    ),
    path("product/add/", views.cfs_add_product, name="cfs-schedule-add-product"),
    path("product/<int:product_pk>/", include(product_urls)),
]


urlpatterns = [
    # List export applications
    path("", views.ExportApplicationChoiceView.as_view(), name="choose"),
    # common create
    path(
        "create/<exportapplicationtype:type_code>/",
        views.create_export_application,
        name="create-application",
    ),
    # Export application groups
    path(
        "com/<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_com, name="com-edit"),
                path("submit/", views.submit_com, name="com-submit"),
            ]
        ),
    ),
    path(
        "cfs/<int:application_pk>/",
        include(
            [
                path("edit/", views.edit_cfs, name="cfs-edit"),
                path("schedule/add", views.cfs_add_schedule, name="cfs-schedule-add"),
                path("schedule/<int:schedule_pk>/", include(schedule_urls)),
                path("submit/", views.submit_cfs, name="cfs-submit"),
            ]
        ),
    ),
]
