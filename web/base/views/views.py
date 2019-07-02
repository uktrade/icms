from django.core.exceptions import SuspiciousOperation
from django.views.generic.list import ListView
import logging

logger = logging.getLogger(__name__)


def raise_suspicious(message='Invalid request'):
    raise SuspiciousOperation(message)


class PostActionMixin(object):
    """
    Handle post requests with action variable: Calls method with the same name
    as action variable to handle action
    """

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        logger.debug('Form action: "%s", Arguments:[%s]', action, kwargs)
        if action and hasattr(self, action):
            return getattr(self, action)(request, *args, **kwargs)

        return super().__self_class__.__mro__[2].post(
            self, request, *args, **kwargs)


class PostActionView(PostActionMixin):
    def _get_item(self, request, item_param='item'):
        if not (request.POST or request.POST.get(item_param)):
            raise_suspicious()
        id = request.POST.get(item_param)
        return self.model.objects.get(pk=id)

    def archive(self, request):
        if not self.model.Display.archive:
            raise_suspicious()
        self._get_item(request).archive()
        return super().get(request)

    def unarchive(self, request):
        if not self.model.Display.archive:
            raise_suspicious()
        self._get_item(request).unarchive()
        return super().get(request)

    def move_up(self, request):
        item = self._get_item
        if not self.model.Display.sort:
            raise_suspicious()
        item(request).swap_order(item(request, 'prev_item'))
        return super().get(request)

    def move_down(self, request):
        item = self._get_item
        if not self.model.Display.sort:
            raise_suspicious()
        item(request).swap_order(item(request, 'next_item'))
        return super().get(request)


class FilteredListView(PostActionView, ListView):
    def get_queryset(self):
        load_immediate = hasattr(self, 'load_immediate') and self.load_immediate
        if self.request.GET or self.request.POST or load_immediate:
            return self.model.objects.all()
        else:
            return self.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['filter'] = self.filterset_class(
            self.request.GET or None, queryset=self.get_queryset())
        return context
