from django.urls import path, re_path

from web.domains.case._import.views import (
    ImportApplicationChoiceView,
    archive_user_import_certificate_file,
    case_oil_view,
    create_import_contact,
    create_oil,
    create_user_import_certificate,
    edit_import_contact,
    edit_oil,
    edit_user_import_certificate,
    list_import_contacts,
    list_user_import_certificates,
    submit_oil,
    toggle_verified_firearms,
    validate_oil,
    view_verified_firearms,
)

urlpatterns = [
    path("", ImportApplicationChoiceView.as_view(), name="new-import-application"),
    # Firearms and Ammunition - Open Individual Licence
    path("firearms/oil/create/", create_oil, name="create-oil"),
    path("firearms/oil/<int:pk>/edit/", edit_oil, name="edit-oil"),
    path("firearms/oil/<int:pk>/validation/", validate_oil, name="oil-validation"),
    path("firearms/oil/<int:pk>/submit/", submit_oil, name="submit-oil"),
    # Firearms and Ammunition - Application made by user
    path("case/firearms/oil/<int:pk>/view/", case_oil_view, name="view-oil-case"),
    # Firearms and Ammunition - User Certificates
    path(
        "firearms/oil/<int:pk>/certificates/",
        list_user_import_certificates,
        name="list-user-import-certificates",
    ),
    path(
        "firearms/oil/<int:pk>/certificates/create/",
        create_user_import_certificate,
        name="create-user-import-certificate",
    ),
    path(
        "firearms/oil/<int:application_pk>/certificates/<int:certificate_pk>/edit/",
        edit_user_import_certificate,
        name="edit-user-import-certificate",
    ),
    path(
        "firearms/oil/<int:application_pk>/certificates/<int:certificate_pk>/files/<int:file_pk>/archive/",
        archive_user_import_certificate_file,
        name="archive-user-import-certificate-file",
    ),
    # Firearms and Ammunition - Verified Certificates
    path(
        "verified-firearms/oil/<int:application_pk>/firearms/<int:firearms_pk>/toggle/",
        toggle_verified_firearms,
        name="toggle-verified-firearms",
    ),
    path(
        "verified-firearms/oil/<int:application_pk>/firearms/<int:firearms_pk>/view/",
        view_verified_firearms,
        name="view-verified-firearms",
    ),
    # Firearms and Ammunition - Import Contact
    path(
        "firearms/oil/<int:pk>/import-contacts/",
        list_import_contacts,
        name="list-import-contacts",
    ),
    re_path(
        "^firearms/oil/(?P<pk>[0-9]+)/import-contacts/(?P<entity>legal|natural)/create/$",
        create_import_contact,
        name="create-import-contact",
    ),
    re_path(
        "^firearms/oil/(?P<application_pk>[0-9]+)/import-contacts/(?P<entity>legal|natural)/(?P<contact_pk>[0-9]+)/edit/$",
        edit_import_contact,
        name="edit-import-contact",
    ),
]
