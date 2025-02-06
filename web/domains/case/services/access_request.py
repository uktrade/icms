from web.models import ExporterAccessRequest, ImporterAccessRequest, Task
from web.types import AuthenticatedHttpRequest

from . import reference


def create_import_access_request(
    request: AuthenticatedHttpRequest, access_request: ImporterAccessRequest
) -> ImporterAccessRequest:
    access_request.reference = reference.get_importer_access_request_reference(
        request.icms.lock_manager
    )
    access_request.submitted_by = request.user
    access_request.last_updated_by = request.user
    access_request.process_type = ImporterAccessRequest.PROCESS_TYPE
    access_request.save()

    Task.objects.create(process=access_request, task_type=Task.TaskType.PROCESS, owner=request.user)

    return access_request


def create_export_access_request(
    request: AuthenticatedHttpRequest, access_request: ExporterAccessRequest
) -> ExporterAccessRequest:
    access_request.reference = reference.get_exporter_access_request_reference(
        request.icms.lock_manager
    )
    access_request.submitted_by = request.user
    access_request.last_updated_by = request.user
    access_request.process_type = ExporterAccessRequest.PROCESS_TYPE
    access_request.save()

    Task.objects.create(process=access_request, task_type=Task.TaskType.PROCESS, owner=request.user)

    return access_request
