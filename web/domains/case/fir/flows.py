import structlog as logging
from django.dispatch import receiver
from django.utils.decorators import method_decorator
from viewflow import flow
from viewflow.base import Flow, this

from web.viewflow.nodes import View
from web.viewflow.signals import flow_cancelled

from . import models, views

__all__ = ["FurtherInformationRequestFlow"]


logger = logging.getLogger(__name__)


def send_fir_email(activation):
    pass


def send_fir_response_email(activation):
    pass


class FurtherInformationRequestFlow(Flow):
    """
        Further Information Request

        FIRs are used as parallel flows of different flows and depends on the parent process
        for FIR view permissions.

        Parent process must use .mixins.FurtherInformationRequestMixin for the functional
        interface to read necessary permissions for FIR.

    """

    DRAFT = models.FurtherInformationRequest.DRAFT
    process_template = "web/domains/case/fir/partials/process.html"
    process_class = models.FurtherInformationRequestProcess

    start = flow.StartFunction(this.start_fir).Next(this.check_draft)

    # If draft, create a task for fir requester to finish the request
    check_draft = (
        flow.If(cond=lambda activation: activation.process.fir.is_draft())
        .Then(this.complete_request)
        .Else(this.notify_contacts)
    )

    # for case officer to finish the request if saved as draft
    complete_request = (
        View(views.FutherInformationRequestEditView)
        .Next(this.notify_contacts)
        .Assign(this.start.owner)
    )

    # notify importer/exporter contacts for new fir via email
    notify_contacts = flow.Handler(send_fir_email).Next(this.respond)

    # for importer/exporter contacts to send further information back
    respond = (
        View(views.FurtherInformationRequestResponseView)
        .Team(lambda p: p.parent_process.get_fir_response_team())
        .Next(this.notify_case_officers)
        .Permission(lambda a: a.process.parent_process.get_fir_response_permission())
    )

    # notify case officers of the response
    notify_case_officers = flow.Handler(send_fir_response_email).Next(this.review)

    # for case officer to review and close the fir
    review = (
        View(views.FurtherInformationRequestReviewView)
        .Permission(lambda a: a.process.parent_process.get_fir_starter_permission())
        .Next(this.end)
    )

    end = flow.End()

    @method_decorator(flow.flow_start_func)
    def start_fir(self, activation, parent_process, further_information_request):
        activation.prepare()
        activation.process.parent_process = parent_process
        activation.task.owner = further_information_request.requested_by
        activation.process.fir = further_information_request
        activation.done()


@receiver(flow_cancelled, sender=FurtherInformationRequestFlow)
def delete_fir(sender, **kwargs):
    """
        Set FIR status to DELETED and deactivate if process is cancelled
    """
    logger.debug("Cancel received", sender=sender, kwargs=kwargs)
    process = kwargs.get("process")
    fir = process.fir
    fir.delete()
