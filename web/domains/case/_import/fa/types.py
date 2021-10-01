from typing import Type, Union

from web.domains.case._import.fa_dfl.forms import DFLSupplementaryReportForm
from web.domains.case._import.fa_dfl.models import (
    DFLApplication,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
)
from web.domains.case._import.fa_oil.forms import OILSupplementaryReportForm
from web.domains.case._import.fa_oil.models import (
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OpenIndividualLicenceApplication,
)
from web.domains.case._import.fa_sil.forms import SILSupplementaryReportForm
from web.domains.case._import.fa_sil.models import (
    SILApplication,
    SILSupplementaryInfo,
    SILSupplementaryReport,
)

FaImportApplication = Union[OpenIndividualLicenceApplication, DFLApplication, SILApplication]
FaSupplementaryInfo = Union[DFLSupplementaryInfo, OILSupplementaryInfo, SILSupplementaryInfo]

FaSupplementaryReport = Union[
    DFLSupplementaryReport, OILSupplementaryReport, SILSupplementaryReport
]

FaSupplementaryReportFormT = Type[
    Union[DFLSupplementaryReportForm, OILSupplementaryReportForm, SILSupplementaryReportForm]
]
