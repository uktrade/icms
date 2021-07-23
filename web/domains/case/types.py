from typing import Type, Union

from web.models import (
    AccessRequest,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ImportApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)

ImpOrExp = Union[ImportApplication, ExportApplication]
ImpOrExpT = Type[ImpOrExp]

ImpOrExpOrAccess = Union[ImportApplication, ExportApplication, AccessRequest]
ImpOrExpOrAccessT = Type[ImpOrExpOrAccess]


ApplicationsWithChecklist = Union[
    OpenIndividualLicenceApplication,
    DFLApplication,
    SILApplication,
    WoodQuotaApplication,
    DerogationsApplication,
    OutwardProcessingTradeApplication,
    TextilesApplication,
]
