import structlog as logging
from django.http import HttpResponseRedirect
from django.views.generic.base import View
from django.views.generic.list import ListView

from viewflow.flow.views.start import BaseStartFlowMixin
from viewflow.flow.views.task import BaseFlowMixin

logger = logging.get_logger(__name__)


class PageTitleMixin(View):
    """
    Adds page title attribute of view to context
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # Try get_page_title method first which takes precedence
        page_title = getattr(self, 'get_page_title', None)
        if page_title:
            page_title = page_title()
        else:
            # Get page_title attribute if get_page_title doesn't exist
            page_title = getattr(self, 'page_title', None)
        context['page_title'] = page_title
        return context


class DataDisplayConfigMixin(PageTitleMixin, ListView):
    """
    Adds display configuration for listed object
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        display = getattr(self, 'Display', None)
        if display:
            context['display'] = display
        return context

class PostActionMixin(View):
    """
    Handle post requests with action variable: Calls method with the same name
    as action variable to handle action
    """
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            return self.post(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action:
            logger.debug('Received post action', action=action)
            if hasattr(self, action):
                return getattr(self, action)(request, *args, **kwargs)

        # If action does not exist continue with regular post request
        return super().post(self, request, *args, **kwargs)


class SimpleStartFlowMixin(BaseStartFlowMixin):
    """StartFlowMixin without MessageUserMixin"""
    def activation_done(self, *args, **kwargs):
        """Finish task activation."""
        self.activation.done()

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(SimpleStartFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())


class SimpleFlowMixin(BaseFlowMixin):
    """FlowMixin without MessageUserMixin."""
    def activation_done(self, *args, **kwargs):
        """Finish the task activation."""
        self.activation.done()

    def form_valid(self, form, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(SimpleFlowMixin, self).form_valid(form, **kwargs)
        form.save()
        self.activation_done(form, **kwargs)
        return HttpResponseRedirect(self.get_success_url())
