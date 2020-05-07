#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models

from web.domains.file.models import File
from web.domains.user.models import User


class FurtherInformationRequest(models.Model):
    """
    Further information requests for cases requested from
    applicant by case officers
    """

    DRAFT = 'DRAFT'
    CLOSED = 'CLOSED'
    DELETED = 'DELETED'
    OPEN = 'OPEN'
    RESPONDED = 'RESPONDED'

    STATUSES = ((DRAFT, 'Draft'), (CLOSED, 'CLOSED'), (DELETED, 'Deleted'),
                (OPEN, 'Open'), (RESPONDED, 'Responded'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=20,
                              choices=STATUSES,
                              blank=False,
                              null=False,
                              default=DRAFT)
    request_subject = models.CharField(max_length=100, blank=False, null=True)
    request_detail = models.TextField(blank=False, null=True)
    email_cc_address_list = models.CharField(max_length=4000,
                                             blank=True,
                                             null=True)
    requested_datetime = models.DateTimeField(blank=True,
                                              null=True,
                                              auto_now_add=True)
    response_detail = models.CharField(max_length=4000, blank=False, null=True)
    response_datetime = models.DateTimeField(blank=True, null=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='requested_further_import_information')
    response_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='responded_import_information_requests')
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='closed_import_information_requests')
    deleted_datetime = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='deleted_import_information_requests')
    files = models.ManyToManyField(File, blank=True)

    def date_created_formatted(self):
        """
            returns a formatted datetime
        """
        return self.requested_datetime.strftime('%d-%b-%Y %H:%M:%S')

    def has_deleted_files(self):
        return self.files.all().filter(is_active=False).count() > 0
