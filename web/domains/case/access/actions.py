#!/usr/bin/env python
# -*- coding: utf-8 -*-

import structlog as logging
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from web.domains.case.access.models import AccessRequestProcess
from web.views.actions import PostAction

# from viewflow.decorators import flow_func

logger = logging.get_logger(__name__)


class LinkImporter(PostAction):
    action = 'link'
    label = 'Link Importer'
    icon = 'icon-link'
    confirm = False

    def display(self, object):
        return True

    def handle(self, request, model, process_id, task_id):
        access_request = AccessRequestProcess.objects.get(
            pk=process_id).access_request
        importer = self._get_item(request, model)
        logger.debug('Linking importer',
                     access_request=access_request,
                     importer=importer)
        access_request.linked_importer = importer
        access_request.save()
        messages.success(request, 'Linked Importer Successfuly')
        return redirect(reverse('review_request', args=(process_id, task_id)))


class LinkExporter(PostAction):
    action = 'link'
    label = 'Link Exporter'
    icon = 'icon-link'
    confirm = False

    def display(self, object):
        return True

    def handle(self, request, model, process_id, task_id):
        access_request = AccessRequestProcess.objects.get(
            pk=process_id).access_request
        exporter = self._get_item(request, model)
        logger.debug('Linking Exporter',
                     access_request=access_request,
                     exporter=exporter)
        access_request.linked_exporter = exporter
        access_request.save()
        messages.success(request, 'Linked Exporter Successfuly')
        return redirect(reverse('review_request', args=(process_id, task_id)))
