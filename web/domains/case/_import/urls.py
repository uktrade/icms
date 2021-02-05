from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.ImportApplicationChoiceView.as_view(), name="new-import-application"),
    # Firearms and Ammunition - Open Individual Licence
    path("firearms/oil/create/", views.create_oil, name="create-oil"),
    path("firearms/oil/<int:pk>/edit/", views.edit_oil, name="edit-oil"),
    path("firearms/oil/<int:pk>/validation/", views.validate_oil, name="oil-validation"),
    path("firearms/oil/<int:pk>/submit/", views.submit_oil, name="submit-oil"),
    # Firearms and Ammunition - Management by ILB Admin
    path(
        "case/firearms/oil/<int:pk>/take_ownership/",
        views.take_ownership,
        name="case-take-ownership",
    ),
    path(
        "case/firearms/oil/<int:pk>/release_ownership/",
        views.release_ownership,
        name="case-release-ownership",
    ),
    path("case/firearms/oil/<int:pk>/management/", views.manage_case, name="case-management"),
    # Firearms and Ammunition - Application made by user
    path("case/firearms/oil/<int:pk>/view/", views.case_oil_view, name="view-oil-case"),
    path("case/firearms/oil/<int:pk>/withdraw/", views.case_oil_withdraw, name="withdraw-oil-case"),
    path(
        "case/firearms/oil/<int:application_pk>/withdraw/<int:withdrawal_pk>/archive/",
        views.case_oil_withdraw_archive,
        name="archive-withdrawal-oil-case",
    ),
    # Firearms and Ammunition - User Certificates
    path(
        "firearms/oil/<int:pk>/certificates/",
        views.list_user_import_certificates,
        name="list-user-import-certificates",
    ),
    path(
        "firearms/oil/<int:pk>/certificates/create/",
        views.create_user_import_certificate,
        name="create-user-import-certificate",
    ),
    path(
        "firearms/oil/<int:application_pk>/certificates/<int:certificate_pk>/edit/",
        views.edit_user_import_certificate,
        name="edit-user-import-certificate",
    ),
    path(
        "firearms/oil/<int:application_pk>/certificates/<int:certificate_pk>/files/<int:file_pk>/archive/",
        views.archive_user_import_certificate_file,
        name="archive-user-import-certificate-file",
    ),
    # Firearms and Ammunition - Verified Certificates
    path(
        "verified-firearms/oil/<int:application_pk>/firearms/<int:firearms_pk>/toggle/",
        views.toggle_verified_firearms,
        name="toggle-verified-firearms",
    ),
    path(
        "verified-firearms/oil/<int:application_pk>/firearms/<int:firearms_pk>/view/",
        views.view_verified_firearms,
        name="view-verified-firearms",
    ),
    # Firearms and Ammunition - Import Contact
    path(
        "firearms/oil/<int:pk>/import-contacts/",
        views.list_import_contacts,
        name="list-import-contacts",
    ),
    re_path(
        "^firearms/oil/(?P<pk>[0-9]+)/import-contacts/(?P<entity>legal|natural)/create/$",
        views.create_import_contact,
        name="create-import-contact",
    ),
    re_path(
        "^firearms/oil/(?P<application_pk>[0-9]+)/import-contacts/(?P<entity>legal|natural)/(?P<contact_pk>[0-9]+)/edit/$",
        views.edit_import_contact,
        name="edit-import-contact",
    ),
]
