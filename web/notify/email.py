#!/usr/bin/env python
# -*- coding: utf-8 -*-

from config.celery import app
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.user.models import User

from . import utils


@app.task(name="web.notify.email.send_email")
def send_email(subject, message, recipients, html_message=None, cc_list=None):
    utils.send_email(subject, message, recipients, html_message=html_message, cc_list=cc_list)


def send_to_importers(subject, message, html_message=None):
    importers = Importer.objects.filter(is_active=True)
    for importer in importers:
        if importer.type == Importer.INDIVIDUAL:
            if importer.user.account_status == User.ACTIVE:
                send_email.delay(
                    subject,
                    message,
                    utils.get_notification_emails(importer.user),
                    html_message=html_message,
                )
        else:  # Importer organisation
            for user in importer.members.filter(account_status=User.ACTIVE):
                send_email.delay(
                    subject, message, utils.get_notification_emails(user), html_message=html_message
                )


def send_to_exporters(subject, message, html_message=None):
    exporters = Exporter.objects.filter(is_active=True)
    for exporter in exporters:
        for user in exporter.members.filter(account_status=User.ACTIVE):
            send_email.delay(
                subject, message, utils.get_notification_emails(user), html_message=html_message
            )


@app.task(name="web.notify.email.send_to_import_case_officers")
def send_to_import_case_officers(subject, message, html_message=None):
    recipients = utils.get_import_case_officers_emails()
    send_email.delay(subject, message, recipients, html_message=html_message)


@app.task(name="web.notify.email.send_to_export_case_officers")
def send_to_export_case_officers(subject, message, html_message=None):
    recipients = utils.get_export_case_officers_emails()
    send_email.delay(subject, message, recipients, html_message=html_message)


@app.task(name="web.notify.email.send_mailshot")
def send_mailshot(subject, message, html_message=None, to_importers=False, to_exporters=False):
    """
        Sends mailshots
    """
    if to_importers:
        send_to_importers(subject, message, html_message=html_message)
    if to_exporters:
        send_to_exporters(subject, message, html_message=html_message)
