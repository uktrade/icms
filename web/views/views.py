from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from web.auth.decorators import require_registered
from web.auth.mixins import RequireRegisteredMixin

from .mixins import PostActionMixin, DataDisplayConfigMixin, PageTitleMixin


@require_registered
def home(request):
    return render(request, 'web/home.html')


class ModelFilterView(PostActionMixin, RequireRegisteredMixin,
                      DataDisplayConfigMixin, ListView):
    paginate_by = 50

    def archive(self, *args, **kwargs):
        item = self.request.POST.get('item')
        self.model.objects.get(pk=item).archive()
        messages.success(self.request, 'Record archived successfully')
        return super().get(*args, **kwargs)

    def unarchive(self, *args, **kwargs):
        item = self.request.POST.get('item')
        self.model.objects.get(pk=item).unarchive()
        messages.success(self.request, 'Record unarchived successfully')
        return super().get(*args, **kwargs)

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


class ModelCreateView(RequireRegisteredMixin, PageTitleMixin,
                      SuccessMessageMixin, CreateView):
    success_message = "Record created successfully"
    template_name = 'model/edit.html'


class ModelUpdateView(RequireRegisteredMixin, PageTitleMixin,
                      SuccessMessageMixin, UpdateView):
    success_message = "Record updated successfully"
    template_name = 'model/edit.html'


class ModelDetailView(RequireRegisteredMixin, PageTitleMixin, DetailView):
    template_name = 'model/view.html'

    def _readonly(self, form):
        for key in form.fields.keys():
            form.fields[key].disabled = True
        return form

    def get_form(self, instance=None):
        """Create new instance of form and make readonly"""
        form = self.form_class(instance=instance)
        return self._readonly(form)

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = self.get_form(instance=object)
        return context
