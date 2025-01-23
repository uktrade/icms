from django.urls import include, path

from . import views

app_name = "ecil"
urlpatterns = [
    path("gds-example/", views.GDSTestPageView.as_view(), name="gds_example"),
    path("gds-form-example/", views.GDSFormView.as_view(), name="gds_form_example"),
    path(
        "gds-model-form-example/", views.GDSModelFormView.as_view(), name="gds_model_form_example"
    ),
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
