import structlog as logging
from django.urls import reverse_lazy

from web.views import (ModelCreateView, ModelDetailView, ModelFilterView,
                       ModelUpdateView)
from web.views.actions import Archive, Edit, Unarchive
from web.views.mixins import PostActionMixin

from .forms import (ObsoleteCalibreGroupDisplayForm,
                    ObsoleteCalibreGroupEditForm, ObsoleteCalibreGroupFilter,
                    new_calibres_formset)
from .models import ObsoleteCalibreGroup

permissions = 'web.IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL'

logger = logging.getLogger(__name__)


class ObsoleteCalibreListView(PostActionMixin, ModelFilterView):
    template_name = 'web/domains/firearms/group/list.html'
    filterset_class = ObsoleteCalibreGroupFilter
    model = ObsoleteCalibreGroup
    page_title = 'Maintain Obsolete Calibres'
    permission_required = permissions
    paginate = False

    def swap_orders(self, first, second):
        order = first.order
        first.order = second.order
        second.order = order
        first.save()
        second.save()

    def move_up(self, request, *args, **kwargs):
        pk = request.POST.get('item')
        previous_pk = request.POST.get('previtem')
        groups = ObsoleteCalibreGroup.objects.filter(pk__in=[pk, previous_pk])
        self.swap_orders(groups.first(), groups.last())
        return super().get(request)

    def move_down(self, request, *args, **kwargs):
        pk = request.POST.get('item')
        next_pk = request.POST.get('nextitem')
        groups = ObsoleteCalibreGroup.objects.filter(pk__in=[pk, next_pk])
        self.swap_orders(groups.first(), groups.last())
        return super().get(request)

    class Display:
        fields = ['name', 'calibres__count']
        fields_config = {
            'name': {
                'header': 'Obsolete Calibre Group Name'
            },
            'calibres__count': {
                'header': 'Number of Items',
                'tooltip':
                'The total number of obsolete calibres in this group'
            }
        }
        actions = [Edit(), Archive(), Unarchive()]


class ObsoleteCalibreGroupBaseView(PostActionMixin):
    def get_formset(self):
        extra = 1
        queryset = None
        if self.object:
            queryset = self.object.calibres
            if not self.request.GET.get('display_archived', None):
                queryset = queryset.filter(is_active=True)
            if queryset.count() > 0:
                extra = 0

        return new_calibres_formset(self.object,
                                    queryset=queryset,
                                    data=self.request.POST or None,
                                    extra=extra)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['formset'] = self.get_formset()
        return context

    def form_valid(self, form, formset):
        order = form.instance.order
        if not order:
            last = form.instance.order = ObsoleteCalibreGroup.objects.last()
            if last:
                order = last.order
            else:
                order = 1
        form.instance.order = order
        self.object = form.save()
        formset.save()
        return super().form_valid(form=form)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = super().get_form()
        formset = self.get_formset()
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return super().render_to_response(self.get_context_data(form=form))


class ObsoleteCalibreGroupEditView(ObsoleteCalibreGroupBaseView,
                                   ModelUpdateView):
    template_name = 'web/domains/firearms/group/edit.html'
    form_class = ObsoleteCalibreGroupEditForm
    model = ObsoleteCalibreGroup
    success_url = reverse_lazy('obsolete-calibre-list')
    permission_required = permissions


class ObsoleteCalibreGroupCreateView(ObsoleteCalibreGroupBaseView,
                                     ModelCreateView):
    template_name = 'web/domains/firearms/group/edit.html'
    form_class = ObsoleteCalibreGroupEditForm
    model = ObsoleteCalibreGroup
    success_url = reverse_lazy('obsolete-calibre-list')
    permission_required = permissions

    def get_object(self):
        return None


class ObsoleteCalibreGroupDetailView(ModelDetailView):
    template_name = 'web/domains/firearms/group/view.html'
    model = ObsoleteCalibreGroup
    permission_required = permissions

    def get_context_data(self, object):
        context = super().get_context_data()
        context['form'] = ObsoleteCalibreGroupDisplayForm(instance=object)
        if self.request.GET.get('display_archived'):
            calibres = object.calibres.all()
        else:
            calibres = object.calibres.filter(is_active=True)
        context['calibres'] = calibres
        return context
