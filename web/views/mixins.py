from django.core.exceptions import SuspiciousOperation


class ViewConfigMixin:
    """Adds 'config' dictionary of view class to context.
    Allows adding page title, context header and other information
    specific to implementing view
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        config = getattr(self, 'config', None)
        context['config'] = config

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
