from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from web.auth.decorators import require_registered
from web.auth.mixins import RequireRegisteredMixin
from web.utils import merge_dictionaries as m

from .mixins import ViewConfigMixin


@require_registered
def home(request):
    return render(request, 'web/home.html')


class ModelFilterView(RequireRegisteredMixin, ViewConfigMixin, ListView):
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['filter'] = self.filterset_class(self.request.GET or None,
                                                 queryset=self.get_queryset())
        return context


class ModelCreateView(RequireRegisteredMixin, ViewConfigMixin, CreateView):
    pass


class ModelUpdateView(RequireRegisteredMixin, ViewConfigMixin, UpdateView):
    pass


class ModelDetailView(RequireRegisteredMixin, ViewConfigMixin, DetailView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = getattr(self, 'config', None)
        config = m({'readonly': True}, config)
        self.config = config
