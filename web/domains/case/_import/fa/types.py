from typing import Type, Union

from web.domains.case._import.fa_dfl.forms import (
    DFLSupplementaryReportFirearmForm,
    DFLSupplementaryReportForm,
)
from web.domains.case._import.fa_dfl.models import (
    DFLApplication,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
    DFLSupplementaryReportFirearm,
)
from web.domains.case._import.fa_oil.forms import (
    OILSupplementaryReportFirearmForm,
    OILSupplementaryReportForm,
)
from web.domains.case._import.fa_oil.models import (
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OILSupplementaryReportFirearm,
    OpenIndividualLicenceApplication,
)
from web.domains.case._import.fa_sil.forms import (
    SILSupplementaryReportFirearmForm,
    SILSupplementaryReportForm,
)
from web.domains.case._import.fa_sil.models import (
    SILApplication,
    SILSupplementaryInfo,
    SILSupplementaryReport,
    SILSupplementaryReportFirearm,
)

FaImportApplication = Union[OpenIndividualLicenceApplication, DFLApplication, SILApplication]
FaSupplementaryInfo = Union[DFLSupplementaryInfo, OILSupplementaryInfo, SILSupplementaryInfo]

FaSupplementaryReport = Union[
    DFLSupplementaryReport, OILSupplementaryReport, SILSupplementaryReport
]

FaSupplementaryReportFirearm = Union[
    DFLSupplementaryReportFirearm, OILSupplementaryReportFirearm, SILSupplementaryReportFirearm
]

FaSupplementaryReportFormT = Type[
    Union[DFLSupplementaryReportForm, OILSupplementaryReportForm, SILSupplementaryReportForm]
]

FaSupplementaryReportFirearmFormT = Type[
    Union[
        DFLSupplementaryReportFirearmForm,
        OILSupplementaryReportFirearmForm,
        SILSupplementaryReportFirearmForm,
    ]
]
