from django.urls import reverse_lazy

from web.auth import utils as auth_utils
from web.views import ModelCreateView

from .forms import NewImportApplicationForm
from .models import ImportApplication


class ImportApplicationCreateView(ModelCreateView):
    template_name = 'web/application/import/create.html'
    model = ImportApplication
    # TODO: Change to application form when created
    success_url = reverse_lazy('product-legislation-list')
    cancel_url = success_url
    form_class = NewImportApplicationForm
    page_title = 'Create Import Application'

    def has_permission(self):
        user = self.request.user
        importer_permission = 'IMP_IMPORTER_CONTACTS:EDIT_APP:{id}:IMP_EDIT_APP'
        agent_permission = 'IMP_IMPORTER_AGENT_CONTACTS:EDIT_APP:{id}:IMP_EDIT_APP'
        # TODO: Simplify and optimize importer and agent edit app permission check
        # Will re-iterate with navigation ticket
        return auth_utils.has_team_permission(
            user,
            user.own_importers.filter(is_active=True,
                                      main_importer__isnull=True).all(),
            importer_permission) or auth_utils.has_team_permission(
                user,
                user.own_importers.filter(is_active=True,
                                          main_importer__isnull=False).all(),
                agent_permission) or auth_utils.has_team_permission(
                    user,
                    user.importer_set.filter(is_active=True,
                                             main_importer__isnull=True).all(),
                    importer_permission) or auth_utils.has_team_permission(
                        user,
                        user.importer_set.filter(
                            is_active=True, main_importer__isnull=False).all(),
                        agent_permission)

    def get_form(self):
        if hasattr(self, 'form'):
            return self.form

        if self.request.POST:
            self.form = NewImportApplicationForm(self.request,
                                                 data=self.request.POST)
        else:
            self.form = NewImportApplicationForm(self.request)

        return self.form

    def post(self, request, *args, **kwargs):
        if request.POST:
            if request.POST.get('change', None):
                return super().get(request, *args, **kwargs)

        form = self.get_form()
        form.instance.created_by = request.user

        return super().post(request, *args, **kwargs)
