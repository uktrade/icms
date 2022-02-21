import datetime
from unittest.mock import Mock

import pytest

from web.domains.case.services import reference
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    DerogationsApplication,
    DFLApplication,
    ExportApplicationType,
    ImportApplicationType,
    IronSteelApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    SanctionsAndAdhocApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)


@pytest.fixture
def lock_manager():
    return Mock()


def test_get_application_case_references(
    db, test_import_user, importer, office, exporter, exporter_office, lock_manager
):
    iat = ImportApplicationType.Types
    iast = ImportApplicationType.SubTypes
    eat = ExportApplicationType.Types

    shared = {"created_by": test_import_user, "last_updated_by": test_import_user}
    import_common = shared | {"importer": importer, "importer_office": office}
    export_common = shared | {"exporter": exporter, "exporter_office": exporter_office}

    derogation_app = DerogationsApplication.objects.create(
        process_type=DerogationsApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.DEROGATION),
        **import_common,
    )
    dfl_app = DFLApplication.objects.create(
        process_type=DFLApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.FIREARMS, sub_type=iast.DFL),
        **import_common,
    )
    oil_app = OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.FIREARMS, sub_type=iast.OIL),
        **import_common,
    )
    sil_app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.FIREARMS, sub_type=iast.SIL),
        **import_common,
    )
    iron_app = IronSteelApplication.objects.create(
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.IRON_STEEL),
        **import_common,
    )
    opt_app = OutwardProcessingTradeApplication.objects.create(
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.OPT),
        **import_common,
    )
    sanction_app = SanctionsAndAdhocApplication.objects.create(
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.SANCTION_ADHOC),
        **import_common,
    )
    textile_app = TextilesApplication.objects.create(
        process_type=TextilesApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.TEXTILES),
        **import_common,
    )
    wood_app = WoodQuotaApplication.objects.create(
        process_type=WoodQuotaApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type=iat.WOOD_QUOTA),
        **import_common,
    )

    com_app = CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code=eat.MANUFACTURE),
        **export_common,
    )
    cfs_app = CertificateOfFreeSaleApplication.objects.create(
        process_type=CertificateOfFreeSaleApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code=eat.FREE_SALE),
        **export_common,
    )
    gmp_app = CertificateOfGoodManufacturingPracticeApplication.objects.create(
        process_type=CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code=eat.GMP),
        **export_common,
    )

    year = datetime.date.today().year

    derogation_app.reference = reference.get_application_case_reference(
        lock_manager, derogation_app
    )
    derogation_app.save()
    assert derogation_app.reference == f"IMA/{year}/00001"

    dfl_app.reference = reference.get_application_case_reference(lock_manager, dfl_app)
    dfl_app.save()
    assert dfl_app.reference == f"IMA/{year}/00002"

    oil_app.reference = reference.get_application_case_reference(lock_manager, oil_app)
    oil_app.save()
    assert oil_app.reference == f"IMA/{year}/00003"

    sil_app.reference = reference.get_application_case_reference(lock_manager, sil_app)
    sil_app.save()
    assert sil_app.reference == f"IMA/{year}/00004"

    iron_app.reference = reference.get_application_case_reference(lock_manager, iron_app)
    iron_app.save()
    assert iron_app.reference == f"IMA/{year}/00005"

    opt_app.reference = reference.get_application_case_reference(lock_manager, opt_app)
    opt_app.save()
    assert opt_app.reference == f"IMA/{year}/00006"

    sanction_app.reference = reference.get_application_case_reference(lock_manager, sanction_app)
    sanction_app.save()
    assert sanction_app.reference == f"IMA/{year}/00007"

    textile_app.reference = reference.get_application_case_reference(lock_manager, textile_app)
    textile_app.save()
    assert textile_app.reference == f"IMA/{year}/00008"

    wood_app.reference = reference.get_application_case_reference(lock_manager, wood_app)
    wood_app.save()
    assert wood_app.reference == f"IMA/{year}/00009"

    com_app.reference = reference.get_application_case_reference(lock_manager, com_app)
    com_app.save()
    assert com_app.reference == f"CA/{year}/00001"

    cfs_app.reference = reference.get_application_case_reference(lock_manager, cfs_app)
    cfs_app.save()
    assert cfs_app.reference == f"CA/{year}/00002"

    gmp_app.reference = reference.get_application_case_reference(lock_manager, gmp_app)
    gmp_app.save()
    assert gmp_app.reference == f"GA/{year}/00001"
