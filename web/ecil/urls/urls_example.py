from django.urls import include, path

from web.ecil.views import views_example as views

app_name = "example"
urlpatterns = [
    path("gds-example/", views.GDSTestPageView.as_view(), name="gds_example"),
    path("gds-form-example/", views.GDSFormView.as_view(), name="gds_form_example"),
    path(
        "ecil-example-model-form/",
        views.GDSModelFormCreateView.as_view(),
        name="gds_model_form_example",
    ),
    path("ecil-example-model-list/", views.ECILExampleListView.as_view(), name="ecil_example_list"),
    path(
        "gds-conditional-model-form-example/",
        views.GDSConditionalModelFormView.as_view(),
        name="gds_conditional_model_form_example",
    ),
    path(
        "ecil-step-form/",
        include(
            [
                path("edit/<str:step>/", views.ECILMultiStepFormView.as_view(), name="step_form"),
                path(
                    "summary/",
                    views.ECILMultiStepFormSummaryView.as_view(),
                    name="step_form_summary",
                ),
            ]
        ),
    ),
    path(
        "multi-step-model-list/",
        views.ECILMultiStepExampleListView.as_view(),
        name="multi_step_model_list",
    ),
]
