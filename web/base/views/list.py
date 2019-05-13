from web.auth.mixins import RequireRegisteredMixin
from django.views import generic


class SearchListView(RequireRegisteredMixin, generic.ListView):

    paginate_by = 100
    paginate_orphans = 5
    context_object_name = 'list'
