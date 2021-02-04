class ProcessError(Exception):
    pass


class ProcessInactiveError(ProcessError):
    pass


class ProcessStateError(ProcessError):
    pass


class TaskError(ProcessError):
    pass
