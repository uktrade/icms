from typing import Union

from web.models import DFLApplication, OpenIndividualLicenceApplication, SILApplication

FaImportApplication = Union[OpenIndividualLicenceApplication, DFLApplication, SILApplication]
