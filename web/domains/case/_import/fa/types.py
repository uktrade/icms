from typing import Type, Union

from web.domains.case._import.fa_dfl.forms import (
    DFLSupplementaryInfoForm,
    DFLSupplementaryReportForm,
)
from web.domains.case._import.fa_dfl.models import (
    DFLApplication,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
)
from web.domains.case._import.fa_oil.forms import (
    OILSupplementaryInfoForm,
    OILSupplementaryReportForm,
)
from web.domains.case._import.fa_oil.models import (
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OpenIndividualLicenceApplication,
)
from web.domains.case._import.fa_sil.forms import (
    SILSupplementaryInfoForm,
    SILSupplementaryReportForm,
)
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

FaSupplementaryInfoFormT = Type[
    Union[DFLSupplementaryInfoForm, OILSupplementaryInfoForm, SILSupplementaryInfoForm]
]

FaSupplementaryReportFormT = Type[
    Union[DFLSupplementaryReportForm, OILSupplementaryReportForm, SILSupplementaryReportForm]
]
