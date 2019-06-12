from django.views.generic.base import View
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.core.exceptions import SuspiciousOperation


def raise_suspicious():
    raise SuspiciousOperation('Invalid request')


class ActionView(View):
    """
    Used for creating a view with multiple actions that renders multiple
    templates on single url depending on post parameter 'action'.
    """

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if not action:
            raise HttpResponseBadRequest('Invalid action')

        return getattr(self, action)(request, *args, **kwargs)


class ModelEditActionView(ActionView):
    """
    Allows editing model object with given pk. Apart from saving other actions
    can be performed using POST parameter 'action' and defining methods with
    the action name. All through same path.

    e.g. Adding people to team before saving is possible by passing
    action=add_member which will render people search view, and in turn
    action=search_people will perform the search and render search results page

    See web/views/views.py for all usage examples
    """

    def get_form(self, request, pk):
        if pk:
            instance = self.model.objects.get(pk=pk)
        else:
            instance = None
        return self.form_class(request.POST or None, instance=instance)

    def render_response(self, form):
        return render(self.request, self.template_name, {'form': form})

    def save(self, request, pk=None):
        form = self.get_form(request, pk)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)

        return self.render_response(form)

    def get(self, request, pk=None):
        return self.render_response(self.get_form(request, pk))


class ModelCreateActionView(ModelEditActionView):
    pass


class ModelListActionView(ActionView):
    """
    Model list view with filters for searching and item actions
    """

    def get_filter(self, request):
        filter_data = request.GET or request.POST or None
        return self.filter_class(
            filter_data, queryset=self.model.objects.all())

    def render_response(self, filter, context={}):
        context['filter'] = filter
        return render(self.request, self.template_name, context)

    def search(self, request):
        return self.render_response(self.get_filter(request))

    def get(self, request, pk=None):
        if not request.GET:
            filter = self.filter_class(queryset=self.model.objects.none())
            return self.render_response(filter, {'first_load': True})

        return self.search(request)

    def get_item(self, request):
        if not (request.POST or request.POST.get('item')):
            raise_suspicious()

        id = request.POST.get('item')
        return self.model.objects.get(pk=id)

    def archive(self, request):
        if not self.model.Display.archive:
            raise_suspicious()
        self.get_item(request).archive()
        return self.render_response(self.get_filter(request))

    def unarchive(self, request):
        if not self.model.Display.archive:
            raise_suspicious()
        self.get_item(request).unarchive()
        return self.render_response(self.get_filter(request))
