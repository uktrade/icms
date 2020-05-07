#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib import messages

from web.notify import notify
from web.views.actions import PostAction

from .models import User


class ReIssuePassword(PostAction):
    action = 're_issue_password'
    label = 'Re-Issue Password'
    confirm = False
    confirm_message = ''
    icon = 'icon-key'

    def display(self, user):
        return user.account_status in [User.ACTIVE, User.SUSPENDED]

    def handle(self, request, view):
        user = self._get_item(request, view.model)
        temp_pass = user.set_temp_password()
        user.account_status = User.ACTIVE
        user.account_status_by = request.user
        user.save()
        notify.register(request, user, temp_pass)
        messages.success(request,
                         'Temporary password successfully issued for account')


class CancelUser(PostAction):
    action = 'cancel'
    label = 'Cancel'
    confirm = True
    confirm_message = 'Are you sure you want to cancel this account?'
    icon = 'icon-bin'

    def display(self, user):
        return user.account_status != User.CANCELLED

    def handle(self, request, view):
        user = self._get_item(request, view.model)
        user.account_status = User.CANCELLED
        user.account_status_by = request.user
        user.save()
        messages.success(request, 'Account cancelled successfully')


class ActivateUser(PostAction):
    action = 'activate'
    label = 'Activate'
    confirm = True
    confirm_message = 'Are you sure you want to activate this account?'
    icon = 'icon-eye'

    def display(self, user):
        return user.account_status == User.BLOCKED

    def handle(self, request, view):
        user = self._get_item(request, view.model)
        user.account_status = User.ACTIVE
        user.account_status_by = request.user
        user.save()
        messages.success(request, 'Account cancelled successfully')


class BlockUser(PostAction):
    action = 'block'
    label = 'Block'
    confirm = True
    confirm_message = 'Are you sure you want to block this account?'
    icon = 'icon-eye-blocked'

    def display(self, user):
        return user.account_status == User.ACTIVE

    def handle(self, request, view):
        user = self._get_item(request, view.model)
        user.account_status = User.BLOCKED
        user.account_status_by = request.user
        user.save()
        messages.success(request, 'Account blocked successfully')
