from web.domains.case._import.fa_dfl.forms import (
    DFLSupplementaryInfoForm,
    DFLSupplementaryReportForm,
)
from web.domains.case._import.fa_oil.forms import (
    OILSupplementaryInfoForm,
    OILSupplementaryReportForm,
)
from web.domains.case._import.fa_sil.forms import (
    SILSupplementaryInfoForm,
    SILSupplementaryReportForm,
)
from web.models import (
    DFLApplication,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OpenIndividualLicenceApplication,
    SILApplication,
    SILSupplementaryInfo,
    SILSupplementaryReport,
)

FaImportApplication = OpenIndividualLicenceApplication | DFLApplication | SILApplication
FaSupplementaryInfo = DFLSupplementaryInfo | OILSupplementaryInfo | SILSupplementaryInfo

FaSupplementaryReport = DFLSupplementaryReport | OILSupplementaryReport | SILSupplementaryReport

FaSupplementaryInfoFormT = type[
    DFLSupplementaryInfoForm | OILSupplementaryInfoForm | SILSupplementaryInfoForm
]

FaSupplementaryReportFormT = type[
    DFLSupplementaryReportForm | OILSupplementaryReportForm | SILSupplementaryReportForm
]
