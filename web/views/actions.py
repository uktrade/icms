from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from web.models.mixins import Archivable, Sortable


class ListAction:
    def _get_item(self, request, model):
        _id = request.POST.get('item')
        return get_object_or_404(model, pk=_id)

    def display(self, object):
        return True


class PostAction(ListAction):
    template = 'model/actions/submit.html'
    confirm = True  # confirm action before submitting

    def as_html(self, object, csrf_token):
        return mark_safe(
            render_to_string(
                self.template, {
                    'icon': getattr(self, 'icon', None),
                    'csrf_token': csrf_token,
                    'object': object,
                    'confirm': self.confirm,
                    'confirm_message': getattr(self, 'confirm_message', None),
                    'action': self.action,
                    'label': self.label
                }))

    def handle(self, request, model, *args):
        raise SuspiciousOperation('Not implemented!')


class LinkAction(ListAction):
    template = 'model/actions/link.html'

    def href(self, object):
        return f'{object.id}/'

    def as_html(self, object, *args):
        return mark_safe(
            render_to_string(
                self.template, {
                    'icon': self.icon or None,
                    'object': object,
                    'label': self.label,
                    'href': self.href(object)
                }))


class View(LinkAction):
    label = 'View'
    icon = 'icon-eye'


class Edit(LinkAction):
    label = 'Edit'
    icon = 'icon-pencil'

    def href(self, object):
        return f'{object.id}/edit/'


class Archive(PostAction):
    action = 'archive'
    label = 'Archive'
    confirm_message = 'Are you sure you want to archive this record?'
    icon = 'icon-bin'

    def display(self, object):
        return isinstance(object, Archivable) and object.is_active

    def handle(self, request, model):
        self._get_item(request, model).archive()
        messages.success(request, 'Record archived successfully')


class Unarchive(PostAction):
    action = 'unarchive'
    label = 'Unarchive'
    confirm_message = 'Are you sure you want to unarchive this record?'
    icon = 'icon-undo2'

    def display(self, object):
        return isinstance(object, Archivable) and not object.is_active

    def handle(self, request, model):
        self._get_item(request, model).unarchive()
        messages.success(request, 'Record unarchived successfully')


class Sort(PostAction):
    action = 'sort'

    def display(self, object):
        return isinstance(object, Sortable)
