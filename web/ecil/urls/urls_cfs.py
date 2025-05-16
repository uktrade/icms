from django.urls import include, path

from web.ecil.views import views_cfs as views

app_name = "export-cfs"
urlpatterns = [
    path(
        "application/<int:application_pk>/",
        include(
            [
                path(
                    "reference/",
                    views.CFSApplicationReferenceUpdateView.as_view(),
                    name="application-reference",
                ),
                path(
                    "contact/",
                    views.CFSApplicationContactUpdateView.as_view(),
                    name="application-contact",
                ),
                path("schedule/", views.CFSScheduleCreateView.as_view(), name="schedule-create"),
                path(
                    "schedule/<int:schedule_pk>/",
                    include(
                        [
                            path(
                                "exporter-status/",
                                views.CFSScheduleExporterStatusUpdateView.as_view(),
                                name="schedule-exporter-status",
                            ),
                            path(
                                "manufacturer-address/",
                                views.CFSScheduleManufacturerAddressUpdateView.as_view(),
                                name="schedule-manufacturer-address",
                            ),
                            path(
                                "brand-name-holder/",
                                views.CFSScheduleBrandNameHolderUpdateView.as_view(),
                                name="schedule-brand-name-holder",
                            ),
                            path(
                                "country-of-manufacture/",
                                views.CFSScheduleCountryOfManufactureUpdateView.as_view(),
                                name="schedule-country-of-manufacture",
                            ),
                            path(
                                "legislation/",
                                views.CFSScheduleAddLegislationUpdateView.as_view(),
                                name="schedule-legislation",
                            ),
                            path(
                                "legislation/add-another/",
                                views.CFSScheduleAddAnotherLegislationFormView.as_view(),
                                name="schedule-legislation-add-another",
                            ),
                            path(
                                "legislation/<legislation_pk>/remove/",
                                views.CFSScheduleConfirmRemoveLegislationFormView.as_view(),
                                name="schedule-legislation-remove",
                            ),
                            path(
                                "product-standard/",
                                views.CFSScheduleProductStandardUpdateView.as_view(),
                                name="schedule-product-standard",
                            ),
                            path(
                                "responsible-person/",
                                views.CFSScheduleStatementIsResponsiblePersonUpdateView.as_view(),
                                name="schedule-is-responsible-person",
                            ),
                            path(
                                "accordance-with-standards/",
                                views.CFSScheduleStatementAccordanceWithStandardsUpdateView.as_view(),
                                name="schedule-accordance-with-standards",
                            ),
                            #
                            # Schedule product views
                            #
                            path(
                                "product/",
                                views.CFSScheduleProductStartTemplateView.as_view(),
                                name="schedule-product-start",
                            ),
                            path(
                                "product/upload-method/",
                                views.CFSScheduleProductAddMethodFormView.as_view(),
                                name="schedule-product-add-method",
                            ),
                            path(
                                "product/add/",
                                views.CFSScheduleProductCreateView.as_view(),
                                name="schedule-product-add",
                            ),
                            path(
                                "product/add-another/",
                                views.CFSScheduleProductAddAnotherFormView.as_view(),
                                name="schedule-product-add-another",
                            ),
                            path(
                                "product/<int:product_pk>/",
                                include(
                                    [
                                        path(
                                            "edit/",
                                            views.CFSScheduleProductUpdateView.as_view(),
                                            name="schedule-product-edit",
                                        ),
                                        path(
                                            "end-use/",
                                            views.CFSScheduleProductEndUseUpdateView.as_view(),
                                            name="schedule-product-end-use",
                                        ),
                                        path(
                                            "remove/",
                                            views.CFSScheduleProductConfirmRemoveFormView.as_view(),
                                            name="schedule-product-remove",
                                        ),
                                        #
                                        # Product type number urls
                                        path(
                                            "type/add/",
                                            views.CFSScheduleProductTypeCreateView.as_view(),
                                            name="schedule-product-type-add",
                                        ),
                                        path(
                                            "type/add-another/",
                                            views.CFSScheduleProductTypeAddAnotherFormView.as_view(),
                                            name="schedule-product-type-add-another",
                                        ),
                                        path(
                                            "type/<int:product_type_pk>/remove/",
                                            views.CFSScheduleProductTypeConfirmRemoveFormView.as_view(),
                                            name="schedule-product-type-remove",
                                        ),
                                        #
                                        # Active ingredient urls
                                        path(
                                            "active-ingredient/add/",
                                            views.CFSScheduleProductActiveIngredientCreateView.as_view(),
                                            name="schedule-product-active-ingredient-add",
                                        ),
                                        # path(
                                        #     "active-ingredient/add-another/",
                                        #     views.CFSScheduleProductActiveIngredientAddAnotherFormView.as_view(),
                                        #     name="schedule-product-active-ingredient-add-another",
                                        # ),
                                        # path(
                                        #     "active-ingredient/<int:active_ingredient_pk>/remove/",
                                        #     views.CFSScheduleProductActiveIngredientConfirmRemoveFormView.as_view(),
                                        #     name="schedule-product-active-ingredient-remove",
                                        # ),
                                    ]
                                ),
                            ),
                        ],
                    ),
                ),
            ]
        ),
    ),
]
