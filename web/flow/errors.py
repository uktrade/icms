from django.core.exceptions import PermissionDenied


class ProcessError(PermissionDenied):
    pass


class ProcessInactiveError(ProcessError):
    pass


class ProcessStateError(ProcessError):
    pass


class TaskError(ProcessError):
    pass
