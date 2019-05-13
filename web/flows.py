from viewflow import flow
from viewflow.base import this, Flow

from . import views, models


class AccessRequestFlow(Flow):
    process_class = models.AccessRequestProcess
    request = flow.Start(views.request_access).Next(this.approve)
    approve = flow.View(views.home).Next(flow.End())
