from web.domains.team.mixins import ContactsManagementMixin
from web.views import ModelCreateView, ModelFilterView, ModelUpdateView

from .forms import UsersFilter, UsersForm
from .models import UserAccount


class UsersListView(ModelFilterView):
    template_name = 'web/users/list.html'
    model = UserAccount
    filterset_class = UsersFilter
