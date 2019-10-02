from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from web.auth.decorators import require_registered
from web.auth.mixins import RequireRegisteredMixin
from web.utils import merge_dictionaries as m

from .mixins import DataDisplayConfigMixin, ViewConfigMixin


@require_registered
def home(request):
    return render(request, 'web/home.html')


class ModelFilterView(RequireRegisteredMixin, DataDisplayConfigMixin,
                      ListView):
    paginate_by = 50

    def paginate(self, queryset):
        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        f = self.filterset_class(self.request.GET or None,
                                 queryset=self.get_queryset())
        context['filter'] = f
        context['page'] = self.paginate(f.qs)
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
