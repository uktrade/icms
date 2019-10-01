from django.core.exceptions import SuspiciousOperation
from django.views.generic.list import ListView


class ViewConfigMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        config = getattr(self, 'config', None)
        context['config'] = config

        return context


class DataDisplayConfigMixin(ListView):
    """
    Adds display configuration for listed object
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        display = getattr(self, 'Display', None)
        if display:
            context['display_config'] = display
        return context


class PostActionMixin(object):
    """
    Handle post requests with action variable: Calls method with the same name
    as action variable to handle action
    """
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action:
            if hasattr(self, action):
                return getattr(self, action)(request, *args, **kwargs)

        raise SuspiciousOperation('Invalid Request!')
