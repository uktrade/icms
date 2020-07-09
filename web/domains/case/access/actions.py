#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.contrib import messages
from django.shortcuts import redirect
from viewflow.flow.views.utils import get_next_task_url

from web.views.actions import PostAction

logger = logging.get_logger(__name__)


class LinkImporter(PostAction):
    action = "link"
    label = "Link Importer"
    icon = "icon-link"
    confirm = False
    template = "web/domains/case/access/partials/link-action.html"

    def display(self, object):
        return True

    def handle(self, request, view, *args, **kwargs):
        importer = self._get_item(request, view.model)
        access_request = view.activation.process.access_request
        logger.debug("Linking importer", access_request=access_request, importer=importer)
        access_request.linked_importer = importer
        access_request.save()
        view.activation.done()
        messages.success(request, "Linked Importer Successfuly")
        return redirect(get_next_task_url(request, view.activation.process))

    def get_context_data(self, object, csrf_token, **kwargs):
        activation = kwargs.pop("activation")
        context = super().get_context_data(object, csrf_token, **kwargs)
        context["activation"] = activation
        return context


class LinkExporter(LinkImporter):
    label = "Link Exporter"

    def handle(self, request, view):
        exporter = self._get_item(request, view.model)
        access_request = view.activation.process.access_request
        logger.debug("Linking Exporter", access_request=access_request, exporter=exporter)
        access_request.linked_exporter = exporter
        access_request.save()
        view.activation.done()
        messages.success(request, "Linked Exporter Successfuly")
        return redirect(get_next_task_url(request, view.activation.process))
