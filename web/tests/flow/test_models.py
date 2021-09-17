import pytest

from web.flow import errors
from web.flow.models import Process, Task
from web.tests.domains.case.access.factories import ImporterAccessRequestFactory

from .factories import TaskFactory


@pytest.mark.django_db
def test_get_task():
    process = ImporterAccessRequestFactory.create(status="submitted")
    task = TaskFactory.create(process=process, task_type=Task.TaskType.PROCESS)

    active_task = process.get_task("submitted", "process")
    assert active_task == task

    active_task = process.get_task(["withdraw", "submitted"], "process")
    assert active_task == task


@pytest.mark.django_db
def test_get_task_error():
    process = ImporterAccessRequestFactory.create(is_active=False, status="submitted")

    with pytest.raises(errors.ProcessInactiveError) as excinfo:
        process.get_task("submitted", "process")
    assert "Process is not active" in str(excinfo.value)

    process.is_active = True
    process.save()

    with pytest.raises(errors.ProcessStateError) as excinfo:
        process.get_task("withdraw", "process")
    assert f"Process is in the wrong state: {process.status}" in str(excinfo.value)

    tasks = TaskFactory.create_batch(2, process=process, task_type=Task.TaskType.PREPARE)

    with pytest.raises(errors.TaskError) as excinfo:
        process.get_task("submitted", "process")
    assert f"Expected one active task, got {len(tasks)}"


@pytest.mark.django_db
def test_downcast_unknown():
    p = Process(process_type="blaa")

    with pytest.raises(NotImplementedError, match="Unknown process_type blaa"):
        p.get_specific_model()
