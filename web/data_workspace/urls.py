from django.urls import include, path

from . import views

app_name = "data-workspace"

# To add a new version number, see DataWorkspaceVersionConverter in web/converters.py

urlpatterns = [
    path("table-metadata/", views.MetadataView.as_view(), name="metadata"),
    path(
        "<dwversion:version>/",
        include(
            [
                # User urls
                path("exporters/", views.ExporterDataView.as_view(), name="exporter-data"),
                path("importers/", views.ImporterDataView.as_view(), name="importer-data"),
                path("offices/", views.OfficeDataView.as_view(), name="office-data"),
                path("users/", views.UserDataView.as_view(), name="user-data"),
                path(
                    "user-surveys/",
                    views.UserFeedbackSurveyDataView.as_view(),
                    name="user-survey-data",
                ),
                # Case urls
                # Export application urls
                path(
                    "export-applications/",
                    views.ExportApplicationDataView.as_view(),
                    name="export-application-data",
                ),
                path(
                    "export-certificate-documents/",
                    views.ExportCertificateDocumentDataView.as_view(),
                    name="export-certificate-document-data",
                ),
                path(
                    "com-applications/",
                    views.COMApplicationDataView.as_view(),
                    name="com-application-data",
                ),
                path(
                    "gmp-applications/",
                    views.GMPApplicationDataView.as_view(),
                    name="gmp-application-data",
                ),
                path(
                    "cfs-schedules/",
                    views.CFSScheduleDataView.as_view(),
                    name="cfs-schedule-data",
                ),
                path(
                    "cfs-products/",
                    views.CFSProductDataView.as_view(),
                    name="cfs-product-data",
                ),
                path(
                    "legislations/",
                    views.LegislationDataView.as_view(),
                    name="legislation-data",
                ),
                # Import application urls
                path(
                    "import-applications/",
                    views.ImportApplicationDataView.as_view(),
                    name="import-application-data",
                ),
                path(
                    "import-licence-documents/",
                    views.ImportLicenceDocumentDataView.as_view(),
                    name="import-licence-document-data",
                ),
                path(
                    "fa-dfl-applications/",
                    views.FaDflApplicationDataView.as_view(),
                    name="fa-dfl-application-data",
                ),
                path(
                    "fa-dfl-goods/",
                    views.FaDflGoodsDataView.as_view(),
                    name="fa-dfl-goods-data",
                ),
                path(
                    "fa-oil-applications/",
                    views.FaOilApplicationDataView.as_view(),
                    name="fa-oil-application-data",
                ),
                path(
                    "fa-sil-applications/",
                    views.FaSilApplicationDataView.as_view(),
                    name="fa-sil-application-data",
                ),
                path(
                    "fa-sil-goods-section1/",
                    views.FaSilGoodsSection1DataView.as_view(),
                    name="fa-sil-goods-section1-data",
                ),
                path(
                    "fa-sil-goods-section2/",
                    views.FaSilGoodsSection2DataView.as_view(),
                    name="fa-sil-goods-section2-data",
                ),
                path(
                    "fa-sil-goods-section5/",
                    views.FaSilGoodsSection5DataView.as_view(),
                    name="fa-sil-goods-section5-data",
                ),
                path(
                    "fa-sil-goods-section-legacy/",
                    views.FaSilGoodsSectionLegacyDataView.as_view(),
                    name="fa-sil-goods-section-legacy-data",
                ),
                path(
                    "fa-sil-goods-section-obsolete/",
                    views.FaSilGoodsSectionObsoleteDataView.as_view(),
                    name="fa-sil-goods-section-obsolete-data",
                ),
                path(
                    "fa-sil-goods-section-other/",
                    views.FaSilGoodsSectionOtherDataView.as_view(),
                    name="fa-sil-goods-section-other-data",
                ),
                path(
                    "nuclear-material-applications/",
                    views.NuclearMaterialApplicationDataView.as_view(),
                    name="nuclear-material-application-data",
                ),
                path(
                    "nuclear-material-goods/",
                    views.NuclearMaterialGoodsDataView.as_view(),
                    name="nuclear-material-goods-data",
                ),
                path(
                    "sanctions-applications/",
                    views.SanctionsApplicationDataView.as_view(),
                    name="sanctions-application-data",
                ),
                path(
                    "sanctions-goods/",
                    views.SanctionsGoodsDataView.as_view(),
                    name="sanctions-goods-data",
                ),
            ]
        ),
    ),
]
