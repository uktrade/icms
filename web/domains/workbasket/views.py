from datetime import datetime

from django.shortcuts import render, redirect

from web.auth.decorators import require_registered
from web.domains.case.access.models import AccessRequestProcess, AccessRequest


@require_registered
def workbasket(request):
    process = AccessRequestProcess.objects.filter(access_request__status=AccessRequest.SUBMITTED)
    return render(request, 'web/workbasket.html', {'process_list': process})


def take_ownership(request, process_id):
    process = AccessRequestProcess.objects.get(pk=process_id)

    task = process.task_set.first()

    task.assigned = datetime.now()
    task.owner = request.user
    task.status = "ASSIGNED"
    task.save()

    task.process.accessrequestprocess.access_request.save()

    return redirect(f"/viewflow/workflow/web/accessrequest/{process.id}/review_request/{task.id}/")
