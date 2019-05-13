from viewflow import flow
from viewflow.base import this, Flow

from web.views import views
from web import models


class AccessRequestFlow(Flow):
    process_class = models.AccessRequestProcess
    request = flow.Start(views.request_access).Next(this.approve)
    approve = flow.View(views.home).Next(flow.End())
