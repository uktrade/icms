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
        if not action:
            raise_suspicious('Invalid action')

        logger.debug('Form action: "%s", Arguments:[%s]', action, kwargs)

        return getattr(self, action)(request, *args, **kwargs)


class FilteredListView(PostActionMixin, ListView):
    def _get_item(self, request):
        if not (request.POST or request.POST.get('item')):
            raise_suspicious()
        id = request.POST.get('item')
        return self.filterset_class.Meta.model.objects.get(pk=id)

    def get_queryset(self):
        if self.request.GET or self.request.POST or self.load_immediate:
            return self.filterset_class.Meta.model.objects.all()
        else:
            return self.filterset_class.Meta.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['filter'] = self.filterset_class(
            self.request.GET or None, queryset=self.get_queryset())
        return context

    def archive(self, request):
        if not self.filterset_class.Meta.model.Display.archive:
            raise_suspicious()
        self._get_item(request).archive()
        return super().get(request)

    def unarchive(self, request):
        if not self.filterset_class.Meta.model.Display.archive:
            raise_suspicious()
        self._get_item(request).unarchive()
        return super().get(request)
