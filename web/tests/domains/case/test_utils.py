from django.urls import reverse

from web.domains.case.utils import case_documents_metadata
from web.models import GMPFile


def test_fa_sil_document_metadata(fa_sil_app_submitted, section5_authority, firearms_authority):
    # Add authorities to app
    fa_sil_app_submitted.verified_section5.add(section5_authority)
    fa_sil_app_submitted.verified_certificates.add(firearms_authority)

    app = fa_sil_app_submitted
    file_metadata = case_documents_metadata(app)

    assert app.verified_section5.count() == 1
    verified_s5 = app.verified_section5.first()

    assert verified_s5.files.count() == 2
    v_s5_f1, v_s5_f2 = verified_s5.files.all()[:]

    assert app.user_section5.count() == 1
    u_s5_f = app.user_section5.first()

    assert app.verified_certificates.count() == 1
    verified_cert = app.verified_certificates.first()

    assert verified_cert.files.count() == 2
    v_cert_f1, v_cert_f2 = verified_cert.files.all()[:]

    assert app.user_imported_certificates.count() == 1
    u_cert_f = app.user_imported_certificates.first()

    assert file_metadata == {
        v_s5_f1.pk: {
            "title": "Verified Section 5 Authority",
            "reference": "Test Reference",
            "certificate_type": "Section 5 Authority",
            "issuing_constabulary": "",
            "url": get_file_url(
                verified_s5, v_s5_f1, "importer-section5-view-document", model_kwarg="section5_pk"
            ),
        },
        v_s5_f2.pk: {
            "title": "Verified Section 5 Authority",
            "reference": "Test Reference",
            "certificate_type": "Section 5 Authority",
            "issuing_constabulary": "",
            "url": get_file_url(
                verified_s5, v_s5_f2, "importer-section5-view-document", model_kwarg="section5_pk"
            ),
        },
        u_s5_f.pk: {
            "title": "User Uploaded Section 5 Authority",
            "reference": "",
            "certificate_type": "Section 5 Authority",
            "issuing_constabulary": "",
            "url": get_file_url(
                app, u_s5_f, "import:fa-sil:view-section5-document", doc_kwarg="section5_pk"
            ),
        },
        v_cert_f1.pk: {
            "title": "Verified Firearms Authority",
            "reference": "Test Reference",
            "certificate_type": "Deactivation Certificate",
            "issuing_constabulary": "Derbyshire",
            "url": get_file_url(
                verified_cert,
                v_cert_f1,
                "importer-firearms-view-document",
                model_kwarg="firearms_pk",
            ),
        },
        v_cert_f2.pk: {
            "title": "Verified Firearms Authority",
            "reference": "Test Reference",
            "certificate_type": "Deactivation Certificate",
            "issuing_constabulary": "Derbyshire",
            "url": get_file_url(
                verified_cert,
                v_cert_f2,
                "importer-firearms-view-document",
                model_kwarg="firearms_pk",
            ),
        },
        u_cert_f.pk: {
            "title": "User Uploaded Verified Firearms Authority",
            "reference": "Certificate Reference Value",
            "certificate_type": "Registered Firearms Dealer Certificate",
            "issuing_constabulary": "Avon & Somerset",
            "url": get_file_url(
                app, u_cert_f, "import:fa:view-certificate-document", doc_kwarg="certificate_pk"
            ),
        },
    }


def test_fa_oil_document_metadata(fa_oil_app_submitted, firearms_authority):
    # Add authorities to app
    fa_oil_app_submitted.verified_certificates.add(firearms_authority)

    app = fa_oil_app_submitted
    file_metadata = case_documents_metadata(app)

    assert app.verified_certificates.count() == 1
    verified_cert = app.verified_certificates.first()

    assert verified_cert.files.count() == 2
    v_cert_f1, v_cert_f2 = verified_cert.files.all()[:]

    assert app.user_imported_certificates.count() == 1
    u_cert_f = app.user_imported_certificates.first()

    assert file_metadata == {
        v_cert_f1.pk: {
            "title": "Verified Firearms Authority",
            "reference": "Test Reference",
            "certificate_type": "Deactivation Certificate",
            "issuing_constabulary": "Derbyshire",
            "url": get_file_url(
                verified_cert,
                v_cert_f1,
                "importer-firearms-view-document",
                model_kwarg="firearms_pk",
            ),
        },
        v_cert_f2.pk: {
            "title": "Verified Firearms Authority",
            "reference": "Test Reference",
            "certificate_type": "Deactivation Certificate",
            "issuing_constabulary": "Derbyshire",
            "url": get_file_url(
                verified_cert,
                v_cert_f2,
                "importer-firearms-view-document",
                model_kwarg="firearms_pk",
            ),
        },
        u_cert_f.pk: {
            "title": "User Uploaded Verified Firearms Authority",
            "reference": "Certificate Reference Value",
            "certificate_type": "Registered Firearms Dealer Certificate",
            "issuing_constabulary": "Avon & Somerset",
            "url": get_file_url(
                app, u_cert_f, "import:fa:view-certificate-document", doc_kwarg="certificate_pk"
            ),
        },
    }


def test_fa_dfl_document_metadata(fa_dfl_app_submitted, firearms_authority):
    app = fa_dfl_app_submitted
    file_metadata = case_documents_metadata(app)

    assert app.goods_certificates.count() == 1
    file = app.goods_certificates.first()

    assert file_metadata == {
        file.pk: {
            "title": "Firearms Certificate",
            "reference": "deactivated_certificate_reference value",
            "certificate_type": "Deactivation Certificate",
            "issuing_constabulary": "Derbyshire",
            "url": get_file_url(app, file, "import:fa-dfl:view-goods"),
        }
    }


def test_sanctions_document_metadata(sanctions_app_submitted):
    app = sanctions_app_submitted
    file_metadata = case_documents_metadata(app)

    assert app.supporting_documents.count() == 1
    file = app.supporting_documents.first()

    assert file_metadata == {
        file.pk: {
            "file_type": "Supporting Documents",
            "url": get_file_url(app, file, "import:sanctions:view-supporting-document"),
        }
    }


def test_gmp_document_metadata(gmp_app_submitted):
    app = gmp_app_submitted
    file_metadata = case_documents_metadata(app)

    assert app.supporting_documents.count() == 3

    file_17065 = app.supporting_documents.get(file_type=GMPFile.Type.ISO_17065)
    file_17021 = app.supporting_documents.get(file_type=GMPFile.Type.ISO_17021)
    file_22716 = app.supporting_documents.get(file_type=GMPFile.Type.ISO_22716)

    assert file_metadata == {
        file_17065.pk: {
            "file_type": "ISO 17065",
            "url": get_file_url(app, file_17065, "export:gmp-view-document"),
        },
        file_17021.pk: {
            "file_type": "ISO 17021",
            "url": get_file_url(app, file_17021, "export:gmp-view-document"),
        },
        file_22716.pk: {
            "file_type": "ISO 22716",
            "url": get_file_url(app, file_22716, "export:gmp-view-document"),
        },
    }


def test_gmp_document_metadata_for_brc_gsocp_document(gmp_app_submitted, importer_one_contact):
    gmp_app_submitted.gmp_certificate_issued = gmp_app_submitted.CertificateTypes.ISO_22716
    gmp_app_submitted.save()

    gmp_app_submitted.supporting_documents.all().delete()
    gmp_app_submitted.supporting_documents.add(
        GMPFile.objects.create(
            file_type=GMPFile.Type.BRC_GSOCP,
            is_active=True,
            filename="gmp-dummy-file",
            content_type=".txt",
            file_size=2,
            path="gmp-dummy-file-path",
            created_by=importer_one_contact,
        )
    )

    app = gmp_app_submitted
    file_metadata = case_documents_metadata(app)

    assert app.supporting_documents.count() == 1

    file_brc_gsocp = app.supporting_documents.get(file_type=GMPFile.Type.BRC_GSOCP)

    assert file_metadata == {
        file_brc_gsocp.pk: {
            "file_type": "BRC Global Standard for Consumer Products",
            "url": get_file_url(app, file_brc_gsocp, "export:gmp-view-document"),
        }
    }


def get_file_url(model, doc, view_name, model_kwarg="application_pk", doc_kwarg="document_pk"):
    return reverse(
        view_name,
        kwargs={model_kwarg: model.pk, doc_kwarg: doc.pk},
    )
