from copy import deepcopy

from django.http import HttpResponseRedirect
from viewflow.flow.views.start import BaseStartFlowMixin
from viewflow.flow.views.task import BaseFlowMixin


def merge_dictionaries(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
  both a and bhave a key who's value is a dict then dict_merge is called
  on both values and the result stored in the returned dictionary.'''
    if not b:
        return a
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
            result[k] = merge_dictionaries(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result


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

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(SimpleFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())
