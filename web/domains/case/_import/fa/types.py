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
from web.models import SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
from web.models import SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE
from web.models import (
    DFLApplication,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
    DFLSupplementaryReportFirearm,
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OILSupplementaryReportFirearm,
    OpenIndividualLicenceApplication,
    SILApplication,
    SILSupplementaryInfo,
    SILSupplementaryReport,
    SILSupplementaryReportFirearmSection1,
    SILSupplementaryReportFirearmSection2,
    SILSupplementaryReportFirearmSection5,
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

ReportFirearms = (
    SILSupplementaryReportFirearmSection1
    | SILSupplementaryReportFirearmSection2
    | SILSupplementaryReportFirearmSection5
    | SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE
    | SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE
    | DFLSupplementaryReportFirearm
    | OILSupplementaryReportFirearm
)
