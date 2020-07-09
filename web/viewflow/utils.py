#!/usr/bin/env python
# -*- coding: utf-8 -*-
import structlog as logging
from django.template import TemplateSyntaxError
from django.urls import reverse
from django.utils.module_loading import import_string
from viewflow.base import Flow
from viewflow.compat import get_app_package
from viewflow.models import AbstractProcess, AbstractTask

logger = logging.getLogger(__name__)


def get_url(ref, namespace, url_name=None, user=None):
    """
        Viewflow's flowurl Django template tag can not be used with ICMS as ICMS
        use Jinja2 templates.

        This function is adapted from Viewflow sourcecode of flowurl
        template tag.

        See:
        https://github.com/viewflow/viewflow/blob/57eafb964c0d599fba239144e02f739c8c91bb60/viewflow/templatetags/viewflow.py
    """

    if isinstance(ref, Flow):
        url_ref = "{}:{}".format(namespace, url_name if url_name else "index")
        return reverse(url_ref)
    elif isinstance(ref, AbstractProcess):
        kwargs, url_ref = {}, "{}:{}".format(namespace, url_name if url_name else "index")
        if url_name in ["detail", "action_cancel"]:
            kwargs["process_pk"] = ref.pk
        return reverse(url_ref, kwargs=kwargs)
    elif isinstance(ref, AbstractTask):
        return ref.flow_task.get_task_url(
            ref, url_type=url_name if url_name else "guess", user=user, namespace=namespace
        )
    else:
        try:
            app_label, flow_class_path = ref.split("/")
        except ValueError:
            raise TemplateSyntaxError(
                "Flow reference string should  looks like 'app_label/FlowCls' but '{}'".format(ref)
            )

        app_package = get_app_package(app_label)
        if app_package is None:
            raise TemplateSyntaxError("{} app not found".format(app_label))

        import_string("{}.flows.{}".format(app_package, flow_class_path))
        url_ref = "{}:{}".format(namespace, url_name if url_name else "index")
        return reverse(url_ref)
